<template>
  <div class="data-analysis-page">
    <!-- 左侧历史会话栏（仅在非嵌入模式下显示） -->
    <div v-if="viewMode !== 'embed'" class="sidebar-container" :style="{ width: sidebarWidth + 'px' }">
      <HistorySidebar
        @session-selected="handleSessionSelected"
        @session-created="handleSessionCreated"
        @version-selected="handleVersionSelected"
        ref="sidebarRef"
      />
      <!-- 历史会话栏拖拽分隔条 -->
      <div 
        class="sidebar-resize-handle"
        @mousedown="startSidebarResize"
      >
        <div class="resize-handle-line"></div>
      </div>
    </div>

    <!-- 右侧主内容区 -->
    <div class="main-content" :class="{ 'with-dialog': showDialogPanel }">
      <!-- 顶部：标题和操作按钮 -->
      <div class="content-header">
        <div class="header-text">
          <h1>游戏运营数据分析助手</h1>
          <p>上传Excel数据，输入需求即可生成包含图表的运营报告</p>
        </div>
        <div class="header-actions">
          <el-button
            :icon="ArrowLeft"
            @click="goToHome"
          >
            返回首页
          </el-button>
          <el-button
            type="primary"
            :icon="DataAnalysis"
            @click="goToBatchAnalysis"
          >
            批量分析
          </el-button>
          <el-button
            type="primary"
            :icon="DataAnalysis"
            @click="goToCustomBatchAnalysis"
          >
            定制化批量分析
          </el-button>
          <el-button
            type="success"
            :icon="ChatDotRound"
            @click="toggleDialogPanel"
            :class="{ active: showDialogPanel }"
          >
            {{ showDialogPanel ? '隐藏对话' : 'AI对话' }}
          </el-button>
        </div>
      </div>

      <!-- 版本提示条 - 查看历史版本时显示 -->
      <div v-if="isViewingHistory && currentVersion" class="version-banner">
        <el-alert
          type="info"
          :closable="false"
          show-icon
        >
          <template #title>
            <div class="version-banner-content">
              <span>正在查看历史版本 V{{ currentVersion.version_no }}</span>
              <span v-if="currentVersion.summary" class="version-summary">- {{ currentVersion.summary }}</span>
              <span class="version-time">({{ formatVersionTime(currentVersion.created_at) }})</span>
              <el-button 
                type="primary" 
                size="small" 
                @click="returnToCurrentVersion"
                style="margin-left: 16px;"
              >
                返回当前版本
              </el-button>
            </div>
          </template>
        </el-alert>
      </div>

      <!-- 工作流状态提示 -->
      <div class="workflow-status-bar" v-if="!currentWorkflow">
        <el-alert
          title="未配置工作流，请联系管理员"
          type="warning"
          :closable="false"
          show-icon
        />
      </div>
      <div class="workflow-status-bar" v-else>
        <el-tag size="small" type="success">
          <el-icon><Check /></el-icon>
          工作流: {{ currentWorkflow.name }}
        </el-tag>
      </div>

      <!-- 模式切换：上传分析 vs Dify嵌入 -->
      <div class="mode-switch" v-if="currentWorkflow && difyEmbedUrl">
        <el-radio-group v-model="viewMode" size="small">
          <el-radio-button value="upload">上传分析</el-radio-button>
          <el-radio-button value="embed">Dify嵌入</el-radio-button>
        </el-radio-group>
        <el-alert
          v-if="viewMode === 'embed'"
          type="info"
          :closable="false"
          show-icon
          style="margin-top: 12px;"
        >
          <template #title>
            <span style="font-size: 12px;">提示：Dify嵌入模式下，历史对话由Dify内部管理，左侧会话栏已隐藏</span>
          </template>
        </el-alert>
      </div>

      <!-- Dify嵌入模式 -->
      <div v-if="viewMode === 'embed' && difyEmbedUrl" class="dify-embed-container">
        <iframe
          :src="difyEmbedUrl"
          style="width: 100%; height: 100%; min-height: 700px; border: none;"
          frameborder="0"
          allow="microphone"
        ></iframe>
      </div>

      <!-- 上传分析模式 -->
      <template v-if="viewMode === 'upload' || !difyEmbedUrl">
      
      <!-- ========== AI对话模式：左右分栏布局（占满整个主内容区） ========== -->
      <div v-if="showDialogPanel && reportContent" class="dialog-mode-layout">
        <!-- 左侧：对话面板 -->
        <div class="dialog-left-panel" :style="{ width: dialogPanelWidth + 'px' }">
          <DialogPanel
            v-if="currentSessionId"
            ref="dialogPanelRef"
            :session-id="currentSessionId"
            :charts="currentCharts"
            :conversation-id="conversationId"
            :report-text="reportContent?.text || ''"
            :html-charts="reportContent?.html_charts || ''"
            @dialog-response="handleDialogResponse"
            @panel-toggle="toggleDialogPanel"
            @history-cleared="handleHistoryCleared"
            @exit-edit="handleExitEdit"
          />
        </div>
        
        <!-- 拖拽分隔条 -->
        <div 
          class="resize-handle"
          @mousedown="startResize"
          :title="`拖拽调整宽度 (当前: ${dialogPanelWidth}px)`"
        >
          <div class="resize-handle-line"></div>
          <div v-if="isResizing" class="resize-tooltip">
            {{ dialogPanelWidth }}px
          </div>
        </div>
        
        <!-- 右侧：报告展示 -->
        <div class="dialog-right-panel" ref="reportDisplayRef" :style="{ width: `calc(100% - ${dialogPanelWidth}px - 8px)` }">
          <div class="report-display">
            <!-- 报告文字内容 -->
            <div class="report-text report-content-selectable" v-if="reportContent && reportContent.text && typeof reportContent.text === 'string' && !reportContent.text.includes('[object Promise]')">
              <div v-if="isTextFormatting" style="padding: 20px; text-align: center; color: #999;">
                正在格式化文本...
              </div>
              <div v-else v-html="formattedText" class="markdown-content"></div>
            </div>
            
            <!-- 报告操作按钮 - 始终显示 -->
            <div class="chart-action-section" v-if="reportContent">
              <el-tooltip content="当前报告暂无图表" :disabled="!!(reportContent.html_charts && reportContent.html_charts.length > 0)">
                <el-button 
                  type="primary" 
                  :icon="View"
                  size="large"
                  @click="openChartDrawer"
                  :disabled="!reportContent.html_charts || reportContent.html_charts.length === 0"
                >
                  查看图表详情
                </el-button>
              </el-tooltip>
              <el-tooltip content="当前报告暂无图表" :disabled="!!(reportContent.html_charts && reportContent.html_charts.length > 0)">
                <el-button 
                  type="primary" 
                  :icon="Download"
                  size="large"
                  @click="downloadChart"
                  :disabled="!reportContent.html_charts || reportContent.html_charts.length === 0"
                >
                  下载图表
                </el-button>
              </el-tooltip>
              <el-button 
                type="primary" 
                :icon="Download"
                size="large"
                @click="downloadReport"
              >
                下载报告 (PDF)
              </el-button>
            </div>
            
            <!-- HTML图表预览 - 点击进入编辑模式 -->
            <div 
              class="html-charts-preview clickable-chart" 
              v-if="reportContent && reportContent.html_charts && reportContent.html_charts.length > 0"
            >
              <!-- 点击遮罩层 -->
              <div class="chart-click-overlay" @click="handleChartClick">
                <div class="click-hint">
                  <el-icon><Edit /></el-icon>
                  <span>点击编辑图表</span>
                </div>
              </div>
              <iframe
                :srcdoc="reportContent.html_charts"
                class="html-charts-iframe"
                frameborder="0"
                sandbox="allow-scripts allow-same-origin"
              ></iframe>
            </div>
            
            <!-- JSON图表显示（向后兼容） -->
            <div class="report-charts" v-else-if="reportContent && reportContent.charts && reportContent.charts.length > 0">
              <div
                v-for="(_chart, index) in reportContent.charts"
                :key="index"
                class="chart-container"
              >
                <div :id="`chart-${index}`" class="chart"></div>
              </div>
            </div>
          </div>

        </div>
      </div>

      <!-- 查看历史报告模式：只显示报告内容 -->
      <template v-else-if="isViewingHistory && reportContent">
        <div class="history-report-container">
          <!-- 报告显示区（对话形式） -->
          <div class="report-section">
            <div class="report-message">
              <div class="message-avatar">
                <el-icon><DataAnalysis /></el-icon>
              </div>
              <div class="message-content">
                <!-- 报告文字内容 -->
                <div class="report-text" v-if="reportContent && reportContent.text && typeof reportContent.text === 'string' && !reportContent.text.includes('[object Promise]')">
                  <div v-if="isTextFormatting" style="padding: 20px; text-align: center; color: #999;">
                    正在格式化文本...
                  </div>
                  <div v-else v-html="formattedText" class="markdown-content report-content"></div>
                </div>
                
                <!-- 报告操作按钮 - 只读模式 -->
                <div class="chart-action-section" v-if="reportContent">
                  <el-tooltip content="当前报告暂无图表" :disabled="!!(reportContent.html_charts && reportContent.html_charts.length > 0)">
                    <el-button 
                      type="primary" 
                      :icon="View"
                      size="large"
                      @click="openChartDrawer"
                      :disabled="!reportContent.html_charts || reportContent.html_charts.length === 0"
                    >
                      查看图表详情
                    </el-button>
                  </el-tooltip>
                  <el-tooltip content="当前报告暂无图表" :disabled="!!(reportContent.html_charts && reportContent.html_charts.length > 0)">
                    <el-button 
                      type="primary" 
                      :icon="Download"
                      size="large"
                      @click="downloadChart"
                      :disabled="!reportContent.html_charts || reportContent.html_charts.length === 0"
                    >
                      下载图表
                    </el-button>
                  </el-tooltip>
                  <el-button 
                    type="primary" 
                    :icon="Download"
                    size="large"
                    @click="downloadReport"
                  >
                    下载报告 (PDF)
                  </el-button>
                </div>
                
                <!-- 不显示图表预览，只通过按钮打开抽屉查看 -->
              </div>
            </div>
          </div>

        </div>
      </template>

      <!-- 新建分析模式：显示上传区和输入区 -->
      <template v-else>
      <!-- Excel上传区 -->
      <div class="upload-section">
        <el-upload
          ref="uploadRef"
          class="excel-uploader"
          drag
          :auto-upload="false"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          :on-error="handleUploadError"
          accept=".xlsx,.csv"
          :limit="1"
          :file-list="fileList"
          :show-file-list="true"
        >
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">
            <p>拖拽Excel至此处，或点击上传</p>
            <p class="upload-hint">支持.xlsx/.csv，文件大小不超过10MB</p>
          </div>
          <template #tip>
            <div class="upload-tip">
              <el-button 
                type="primary" 
                :icon="Folder"
                @click.stop="triggerFileSelect"
              >
                选择本地文件
              </el-button>
            </div>
          </template>
        </el-upload>
        <div v-if="uploadProgress > 0 && uploadProgress < 100" class="upload-progress">
          <el-progress :percentage="uploadProgress" />
        </div>
      </div>

      <!-- 分析需求输入区 -->
      <div class="input-section">
        <div class="input-header">
          <h3>输入分析需求</h3>
        </div>
        <el-input
          v-model="analysisRequest"
          type="textarea"
          :rows="6"
          placeholder="例如：生成一份关注新手留存的周度报告"
          :maxlength="1000"
          show-word-limit
        />
        <div class="input-examples">
          <el-tag 
            v-for="example in examples" 
            :key="example"
            class="example-tag"
            @click="useExample(example)"
          >
            例: {{ example }}
          </el-tag>
        </div>
        
        <!-- 图表定制 Prompt 输入区（可选） -->
        <div class="chart-customization-section" style="margin-top: 20px;">
          <div class="input-header" style="display: flex; justify-content: space-between; align-items: center;">
            <h3 style="margin: 0;">图表定制 Prompt（可选）</h3>
            <el-switch
              v-model="enableChartCustomization"
              size="small"
              @change="handleChartCustomizationToggle"
            />
          </div>
          <el-input
            v-if="enableChartCustomization"
            v-model="chartCustomizationPrompt"
            type="textarea"
            :rows="4"
            placeholder="请输入图表定制需求，例如：&#10;- 请生成折线图，展示新用户增长趋势&#10;- 使用蓝色主题，添加数据标签&#10;- 图表标题：新用户增长趋势分析&#10;- 图表尺寸：宽度100%，高度700px，宽高比16:9"
            :maxlength="500"
            show-word-limit
            style="margin-top: 10px;"
          />
          <div v-else class="hint-text" style="margin-top: 10px; padding: 10px; background: #f5f7fa; border-radius: 4px; color: #909399; font-size: 12px;">
            💡 开启后可以定制图表样式和类型，例如指定图表类型、颜色主题、数据标签等
          </div>
        </div>
        
        <div class="submit-section">
          <el-button 
            type="primary" 
            size="large"
            :icon="Promotion"
            :loading="isGenerating"
            :disabled="!canSubmit"
            @click="submitAnalysis"
          >
            {{ isGenerating ? '生成中...' : '提交生成报告' }}
          </el-button>
        </div>
      </div>

      <!-- 报告显示区（对话形式）- 新建分析时显示 -->
      <div class="report-section" v-if="reportContent && !isViewingHistory">
        <div class="report-message">
          <div class="message-avatar">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="message-content">
            <!-- 报告文字内容 -->
            <div class="report-text" v-if="reportContent && reportContent.text && typeof reportContent.text === 'string' && !reportContent.text.includes('[object Promise]')">
              <div v-if="isTextFormatting" style="padding: 20px; text-align: center; color: #999;">
                正在格式化文本...
              </div>
              <div v-else-if="formattedText" v-html="formattedText"></div>
              <div v-else style="white-space: pre-wrap; line-height: 1.8;">{{ reportContent.text }}</div>
            </div>
            <div v-else-if="reportContent && reportContent.text && (typeof reportContent.text !== 'string' || reportContent.text.includes('[object Promise]'))" class="report-text-empty">
              <el-alert type="error" :closable="false" show-icon title="报告文字加载异常，请刷新页面重试" />
            </div>
            <div v-else-if="reportContent" class="report-text-empty">
              <el-alert type="warning" :closable="false" show-icon title="文字报告内容为空" />
            </div>
            
            <!-- 报告操作按钮 - 始终显示 -->
            <div class="chart-action-section" v-if="reportContent">
              <el-tooltip content="当前报告暂无图表" :disabled="!!(reportContent.html_charts && reportContent.html_charts.length > 0)">
                <el-button 
                  type="primary" 
                  :icon="View"
                  size="large"
                  @click="openChartDrawer"
                  :disabled="!reportContent.html_charts || reportContent.html_charts.length === 0"
                >
                  查看图表详情
                </el-button>
              </el-tooltip>
              <el-tooltip content="当前报告暂无图表" :disabled="!!(reportContent.html_charts && reportContent.html_charts.length > 0)">
                <el-button 
                  type="primary" 
                  :icon="Download"
                  size="large"
                  @click="downloadChart"
                  :disabled="!reportContent.html_charts || reportContent.html_charts.length === 0"
                >
                  下载图表
                </el-button>
              </el-tooltip>
              <el-button 
                type="primary" 
                :icon="Download"
                size="large"
                @click="downloadReport"
              >
                下载报告 (PDF)
              </el-button>
            </div>
            
            <!-- 可选：保留小预览（iframe） - 点击进入编辑模式 -->
            <div 
              class="html-charts-preview clickable-chart" 
              v-if="reportContent && reportContent.html_charts && reportContent.html_charts.length > 0 && showChartPreview"
            >
              <div class="preview-header">
                <span>图表预览</span>
                <el-button 
                  type="text" 
                  size="small"
                  @click.stop="openChartDrawer"
                >
                  查看大图
                </el-button>
              </div>
              <!-- 点击遮罩层 -->
              <div class="chart-click-overlay" @click="handleChartClick">
                <div class="click-hint">
                  <el-icon><Edit /></el-icon>
                  <span>点击编辑图表</span>
                </div>
              </div>
              <iframe
                :srcdoc="reportContent.html_charts"
                class="html-charts-iframe-preview"
                frameborder="0"
                sandbox="allow-scripts allow-same-origin"
              ></iframe>
            </div>
            
            <!-- JSON图表显示（向后兼容，如果没有html_charts则使用旧方式） -->
            <div class="report-charts" v-else-if="reportContent && reportContent.charts && reportContent.charts.length > 0">
              <div 
                v-for="(_chart, index) in reportContent.charts" 
                :key="index"
                class="chart-container"
              >
                <div :id="`chart-${index}`" class="chart" :ref="el => setChartRef(el, index)"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 流式交互体验说明 -->
      <div class="flow-info" v-if="!reportContent">
        <el-alert
          type="info"
          :closable="false"
          show-icon
        >
          <template #title>
            <div class="flow-info-content">
              <el-icon><Refresh /></el-icon>
              <span>流式交互体验</span>
            </div>
          </template>
          <p>系统会保存每次报告，便于回溯与复用。也可继续提问：如"对比渠道A与渠道B的收入差异"。</p>
        </el-alert>
      </div>
      </template>
      </template>
    </div>

    <!-- 工作流配置弹窗 -->
    <el-dialog
      v-model="showSettings"
      :title="currentWorkflow ? '编辑工作流配置' : '配置工作流'"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form :model="settingsForm" label-width="120px">
        <!-- 步骤1: 选择平台 -->
        <el-form-item label="AI平台">
          <el-radio-group v-model="settingsForm.platform" @change="handlePlatformChange">
            <el-radio-button value="dify">Dify</el-radio-button>
            <el-radio-button value="langchain">Langchain</el-radio-button>
            <el-radio-button value="ragflow">Ragflow</el-radio-button>
            <el-radio-button value="other" disabled>其他（开发中）</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 步骤2: 根据平台显示不同配置 -->
        <template v-if="settingsForm.platform">
          <!-- Dify配置 -->
          <template v-if="settingsForm.platform === 'dify'">
            <el-divider content-position="left">工作流API配置</el-divider>
            
            <el-form-item label="API Key" required>
              <el-input 
                v-model="settingsForm.config.api_key" 
                type="password"
                placeholder="例如: app-G5TRX6MyLsQdfj4V4NRWAplZ"
                show-password
              />
              <template #extra>
                <div style="font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px;">
                  您的Dify API密钥
                </div>
              </template>
            </el-form-item>

            <el-form-item label="文件上传URL" required>
              <el-input 
                v-model="settingsForm.config.url_file" 
                placeholder="例如: http://118.89.16.95/v1/files/upload"
              />
              <template #extra>
                <div style="font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px;">
                  文件上传接口地址
                </div>
              </template>
            </el-form-item>

            <el-form-item label="工作流URL" required>
              <el-input 
                v-model="settingsForm.config.url_work" 
                placeholder="例如: http://118.89.16.95/v1/chat-messages"
              />
              <template #extra>
                <div style="font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px;">
                  工作流执行接口地址
                </div>
              </template>
            </el-form-item>

            <el-form-item label="文件参数名" required>
              <el-input 
                v-model="settingsForm.config.file_param" 
                placeholder="例如: excell"
              />
              <template #extra>
                <div style="font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px;">
                  传入文件的参数名称
                </div>
              </template>
            </el-form-item>

            <el-form-item label="对话参数名" required>
              <el-input 
                v-model="settingsForm.config.query_param" 
                placeholder="例如: query"
              />
              <template #extra>
                <div style="font-size: 12px; color: var(--el-text-color-secondary); margin-top: 4px;">
                  传入对话内容的参数名称
                </div>
              </template>
            </el-form-item>
          </template>

          <!-- Langchain配置 -->
          <template v-if="settingsForm.platform === 'langchain'">
            <el-divider content-position="left">Langchain配置</el-divider>
            
            <el-form-item label="工作流名称" required>
              <el-input v-model="settingsForm.name" placeholder="例如：运营数据分析工作流" />
            </el-form-item>

            <el-form-item label="模型类型" required>
              <el-select v-model="settingsForm.config.model_type" placeholder="选择模型">
                <el-option label="OpenAI" value="openai" />
                <el-option label="Claude" value="claude" />
                <el-option label="本地模型" value="local" />
              </el-select>
            </el-form-item>

            <el-form-item label="API Key" required>
              <el-input 
                v-model="settingsForm.config.api_key" 
                type="password"
                placeholder="输入模型API Key"
                show-password
              />
            </el-form-item>

            <el-form-item label="模型名称">
              <el-input 
                v-model="settingsForm.config.model_name" 
                placeholder="例如：gpt-4, claude-3-opus"
              />
            </el-form-item>

            <el-form-item label="提示词模板">
              <el-input 
                v-model="settingsForm.config.prompt_template" 
                type="textarea"
                :rows="3"
                placeholder="输入提示词模板，使用{input}作为占位符"
              />
            </el-form-item>

            <el-form-item label="描述">
              <el-input 
                v-model="settingsForm.description" 
                type="textarea"
                :rows="2"
                placeholder="可选的工作流描述"
              />
            </el-form-item>
          </template>

          <!-- Ragflow配置 -->
          <template v-if="settingsForm.platform === 'ragflow'">
            <el-divider content-position="left">Ragflow配置</el-divider>
            
            <el-form-item label="工作流名称" required>
              <el-input v-model="settingsForm.name" placeholder="例如：运营数据分析工作流" />
            </el-form-item>

            <el-form-item label="Ragflow API地址" required>
              <el-input 
                v-model="settingsForm.config.api_url" 
                placeholder="https://your-ragflow.com/api"
              />
            </el-form-item>

            <el-form-item label="API Key" required>
              <el-input 
                v-model="settingsForm.config.api_key" 
                type="password"
                placeholder="输入Ragflow API Key"
                show-password
              />
            </el-form-item>

            <el-form-item label="知识库ID">
              <el-input 
                v-model="settingsForm.config.kb_id" 
                placeholder="关联的知识库ID（可选）"
              />
            </el-form-item>

            <el-form-item label="对话模型">
              <el-input 
                v-model="settingsForm.config.chat_model" 
                placeholder="例如：gpt-4"
              />
            </el-form-item>

            <el-form-item label="描述">
              <el-input 
                v-model="settingsForm.description" 
                type="textarea"
                :rows="2"
                placeholder="可选的工作流描述"
              />
            </el-form-item>
          </template>
        </template>

        <el-alert
          v-else
          title="请先选择AI平台"
          type="info"
          :closable="false"
          show-icon
        />
      </el-form>

      <template #footer>
        <el-button @click="showSettings = false">取消</el-button>
        <el-button
          type="primary"
          @click="saveWorkflowConfig"
          :disabled="!canSaveWorkflow"
          :loading="saving"
        >
          {{ currentWorkflow ? '保存配置' : '保存并绑定' }}
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 图表抽屉组件 -->
    <ChartDrawer
      v-model="showChartDrawer"
      :html-content="reportContent?.html_charts"
      title="图表详情"
      @close="handleChartDrawerClose"
    />
    
    <!-- 图表编辑器（全屏模式） -->
    <ChartEditorModal
      v-model="showChartEditor"
      :chart-html="editingChartHtml"
      :chart-title="editingChartTitle"
      :session-id="currentSessionId"
      @save="handleChartEditorSave"
      @cancel="handleChartEditorCancel"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick, markRaw } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElNotification } from 'element-plus'
import {
  Download,
  UploadFilled,
  Folder,
  Promotion,
  DataAnalysis,
  Refresh,
  Check,
  ArrowLeft,
  View,
  ChatDotRound,
  Edit
} from '@element-plus/icons-vue'
import type { UploadFile, UploadInstance } from 'element-plus'
import HistorySidebar from './components/HistorySidebar.vue'
import ChartDrawer from './components/ChartDrawer.vue'
import DialogPanel from './components/DialogPanel.vue'
import ChartEditorModal from '@/components/ChartEditorModal.vue'
import { useOperationStore } from '@/stores/operation'
import {
  uploadExcel,
  generateReport,
  downloadReportPDF,
  getSessionDetail,
  createSession,
  createSessionVersion,
  type Session,
  type ReportResponse,
  type UploadResponse,
  type SessionVersionDetail
} from '@/api/operation'
import { 
  getFunctionWorkflow, 
  bindFunctionWorkflow,
  createWorkflow,
  updateWorkflow
} from '@/api/workflow'
import type { ApiResponse } from '@/types'
import type { AxiosResponse } from 'axios'

// 导入 echarts
import * as echarts from 'echarts'
// 导入 marked 用于 Markdown 渲染
import { marked } from 'marked'

const router = useRouter()
const operationStore = useOperationStore()

const sidebarRef = ref<InstanceType<typeof HistorySidebar> | null>(null)
const uploadRef = ref<UploadInstance | null>(null)

// 查看历史报告模式
const isViewingHistory = ref(false)
const currentVersion = ref<SessionVersionDetail | null>(null)

// 图表抽屉状态
const showChartDrawer = ref(false)
const showChartPreview = ref(true) // 显示图表预览，可点击进入编辑模式

// AI对话面板状态
const showDialogPanel = ref(false)
const currentSessionId = ref<number | null>(null)
const currentCharts = ref<any[]>([])
const conversationId = ref<string>('')
const dialogPanelRef = ref<InstanceType<typeof DialogPanel> | null>(null)
const reportDisplayRef = ref<HTMLElement | null>(null)

// 历史会话栏宽度调整
const sidebarWidth = ref(280) // 默认280px
const isSidebarResizing = ref(false)
const sidebarStartX = ref(0)
const sidebarStartWidth = ref(0)

// 对话面板宽度调整
const dialogPanelWidth = ref(450) // 默认450px
const isResizing = ref(false)
const startX = ref(0)
const startWidth = ref(0)

const fileList = ref<UploadFile[]>([])
const uploadProgress = ref(0)
const analysisRequest = computed({
  get: () => operationStore.analysisRequest,
  set: (val) => operationStore.setAnalysisRequest(val)
})
const isGenerating = computed(() => operationStore.isGenerating)
const canSubmit = computed(() => operationStore.canSubmit)
const reportContent = computed(() => operationStore.reportContent)

// 前端日志系统
const frontendLogger = {
  log: (category: string, message: string, data?: any) => {
    const timestamp = new Date().toISOString()
    const logData = data ? JSON.parse(JSON.stringify(data, (_key, value) => {
      // 处理特殊值，避免循环引用
      if (value instanceof Promise) return '[Promise]'
      if (typeof value === 'function') return '[Function]'
      if (value && typeof value === 'object' && value.constructor && value.constructor.name === 'Map') return '[Map]'
      return value
    })) : undefined
    console.log(`[前端日志][${category}]`, message, logData)
    return { timestamp, category, message, data: logData }
  },
  error: (category: string, message: string, error?: any) => {
    const timestamp = new Date().toISOString()
    console.error(`[前端日志][${category}][错误]`, message, error)
    return { timestamp, category, message, error: error?.message || error }
  }
}

// 格式化后的文本（使用 ref 存储，避免 Promise 问题）
const formattedText = ref<string>('')
const isTextFormatting = ref(false)

// 监听 reportContent.text 变化，异步格式化文本
watch(() => reportContent.value?.text, async (newText) => {
  frontendLogger.log('Watch', 'reportContent.text 变化', {
    hasText: !!newText,
    textType: typeof newText,
    textLength: newText?.length,
    textPreview: newText?.substring(0, 100)
  })
  
  if (!newText || typeof newText !== 'string') {
    frontendLogger.log('Watch', '文本为空或不是字符串，清空格式化文本', {
      newText,
      textType: typeof newText
    })
    formattedText.value = ''
    isTextFormatting.value = false
    return
  }
  
  frontendLogger.log('Watch', '开始格式化文本', {
    length: newText.length,
    preview: newText.substring(0, 100)
  })
  
  isTextFormatting.value = true
  try {
    // marked v5+ 的 parse 方法返回 Promise，必须 await
    marked.setOptions({
      breaks: true,
      gfm: true,
      async: false  // 强制同步模式
    })
    
    // 始终使用 await，因为 instanceof Promise 检查不可靠
    const result = marked.parse(newText)
    const html = (typeof result === 'object' && result !== null && 'then' in result) 
      ? await result 
      : String(result)
    
    frontendLogger.log('Watch', 'marked.parse 完成', {
      htmlLength: html.length,
      htmlPreview: html.substring(0, 100)
    })
    
    // 移除表格
    formattedText.value = html.replace(/<table[\s\S]*?<\/table>/gi, '')
    
    frontendLogger.log('Watch', '格式化完成', {
      finalLength: formattedText.value.length,
      finalPreview: formattedText.value.substring(0, 100)
    })
  } catch (error) {
    frontendLogger.error('Watch', '格式化文本失败', error)
    // 失败时使用简单格式化
    formattedText.value = newText.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    frontendLogger.log('Watch', '使用简单格式化', {
      length: formattedText.value.length,
      isString: typeof formattedText.value === 'string'
    })
  } finally {
    isTextFormatting.value = false
  }
}, { immediate: true })

const examples = [
  '生成一份关注新手留存的周度报告',
  '分析用户活跃度趋势',
  '对比不同渠道的收入表现',
  '生成DAU和MAU的月度分析'
]

const chartInstances = ref<Map<number, any>>(new Map())

// 图表定制相关状态
const enableChartCustomization = ref(false)
const chartCustomizationPrompt = ref('')

// 处理图表定制开关切换
const handleChartCustomizationToggle = (value: boolean | string | number) => {
  if (value === false || value === 0 || value === 'false' || !value) {
    chartCustomizationPrompt.value = ''
  }
}

// 图表编辑相关状态
const showChartEditor = ref(false)
const editingChartHtml = ref('')
const editingChartTitle = ref('')

// 视图模式：upload（上传分析）或 embed（Dify嵌入）
const viewMode = ref<'upload' | 'embed'>('upload')

// Dify嵌入URL
const difyEmbedUrl = computed(() => {
  if (currentWorkflow.value?.config?.embed_url) {
    return currentWorkflow.value.config.embed_url
  }
  return null
})

// 工作流配置相关（简化版，移除权限检查）
const currentWorkflow = ref<any>(null)
const showSettings = ref(false)
const saving = ref(false)
const settingsForm = ref({
  platform: '' as string,
  name: '',
  description: '',
  config: {} as Record<string, any>
})

// 可以保存的条件
const canSaveWorkflow = computed(() => {
  if (!settingsForm.value.platform) return false
  
  const config = settingsForm.value.config
  
  switch (settingsForm.value.platform) {
    case 'dify':
      // 检查用户配置的必需字段
      return !!(config.api_key && config.url_file && config.url_work && config.file_param && config.query_param)
    case 'langchain':
      return config.model_type && config.api_key
    case 'ragflow':
      return config.api_url && config.api_key
    default:
      return false
  }
})

// 切换平台时重置配置
const handlePlatformChange = () => {
  settingsForm.value.config = {}
  settingsForm.value.name = ''
  settingsForm.value.description = ''
}

// 加载工作流配置（静默处理，不显示错误）（简化版，移除project_id参数）
const loadFunctionWorkflow = async () => {
  try {
    const res = await getFunctionWorkflow('operation_data_analysis', true) as unknown as ApiResponse<any>
    if (res.success && res.data) {
      currentWorkflow.value = res.data.workflow
      // 如果配置了嵌入URL，默认显示嵌入模式
      if (res.data.workflow?.config?.embed_url) {
        viewMode.value = 'embed'
      }
    } else {
      currentWorkflow.value = null
    }
  } catch (error: any) {
    // 静默处理404和其他错误，不在控制台显示
    currentWorkflow.value = null
  }
}

// 填充设置表单（用于编辑现有配置）
const fillSettingsForm = () => {
  if (currentWorkflow.value) {
    // 已有配置，填充表单
    const config = currentWorkflow.value.config || {}
    settingsForm.value = {
      platform: 'dify', // 固定为dify
      name: currentWorkflow.value.name || '',
      description: currentWorkflow.value.description || '',
      config: {
        api_key: config.api_key || '',
        url_file: config.url_file || '',
        url_work: config.url_work || '',
        file_param: config.file_param || 'excell',
        query_param: config.query_param || 'query'
      }
    }
  } else {
    // 没有配置，重置表单
    settingsForm.value = {
      platform: 'dify',
      name: '',
      description: '',
      config: {
        api_key: '',
        url_file: '',
        url_work: '',
        file_param: 'excell',
        query_param: 'query'
      }
    }
  }
}

// 打开设置弹窗（简化版，移除权限检查）
// 跳转到批量分析页面
const goToBatchAnalysis = () => {
  router.push({ name: 'operation-batch' })
}

// 跳转到定制化批量分析页面
const goToCustomBatchAnalysis = () => {
  router.push({ name: 'operation-custom-batch' })
}

// 返回首页
const goToHome = () => {
  router.push({ name: 'home' })
}

// AI对话面板相关方法
const toggleDialogPanel = async () => {
  // 如果正在关闭对话面板，检查是否有修改需要保存
  if (showDialogPanel.value) {
    // 关闭对话面板前，询问是否保存版本
    try {
      await ElMessageBox.confirm(
        '是否将当前修改保存为新版本？',
        '保存确认',
        {
          confirmButtonText: '保存为新版本',
          cancelButtonText: '不保存',
          type: 'info',
          distinguishCancelAndClose: true
        }
      )
      
      // 用户确认保存
      if (operationStore.currentSessionId && reportContent.value) {
        try {
          const response = await createSessionVersion(operationStore.currentSessionId, {
            summary: 'AI编辑',
            report_text: reportContent.value.text || '',
            report_html_charts: reportContent.value.html_charts || '',
            report_charts_json: reportContent.value.charts || []
          })
          
          if (response.data) {
            ElMessage.success('已保存为新版本')
            console.log('[DataAnalysis] 已保存为新版本')
            
            // 刷新版本列表
            if (sidebarRef.value) {
              await sidebarRef.value.loadSessions()
            }
          }
        } catch (error) {
          console.error('[DataAnalysis] 保存版本失败:', error)
          ElMessage.error('保存版本失败')
        }
      }
    } catch (action) {
      // 用户取消或选择不保存
      if (action === 'cancel') {
        ElMessage.info('未保存版本')
      }
      console.log('[DataAnalysis] 用户选择不保存版本')
    }
    
    // 关闭对话面板
    showDialogPanel.value = false
    return
  }
  
  // 打开对话面板
  if (!reportContent.value) {
    ElMessage.warning('请先生成报告后再使用AI对话功能')
    return
  }
  
  showDialogPanel.value = true
  if (operationStore.currentSessionId) {
    currentSessionId.value = operationStore.currentSessionId
    console.log('[DataAnalysis] 开启对话模式 - sessionId:', currentSessionId.value)
    // 更新当前图表
    updateCurrentCharts()
  }
}

const updateCurrentCharts = () => {
  // 从报告内容中提取图表配置
  const content = reportContent.value
  console.log('[DataAnalysis] updateCurrentCharts - reportContent:', content)
  
  // 优先使用JSON格式的图表数据（包含完整配置）
  if (content && content.charts && content.charts.length > 0) {
    currentCharts.value = content.charts
    console.log('[DataAnalysis] 使用JSON图表 - 数量:', content.charts.length, '数据:', content.charts)
  } else if (content && content.html_charts) {
    // HTML图表模式：尝试从会话消息中获取原始图表配置
    // 如果没有，创建一个包含HTML内容的虚拟配置
    console.warn('[DataAnalysis] 仅有HTML图表，无结构化配置数据')
    console.warn('[DataAnalysis] AI对话功能需要JSON格式的图表数据才能理解和修改图表')
    console.warn('[DataAnalysis] 建议：在生成报告时使用JSON模式（chart_generation_mode=json）')
    
    // 创建一个虚拟配置，包含HTML内容的基本信息
    currentCharts.value = [{
      type: 'html',
      title: 'AI生成的HTML图表',
      html_content: content.html_charts,
      description: 'HTML格式图表，AI无法直接修改。建议使用JSON模式生成报告。',
      last_modified: 'generated',
      modified_at: new Date().toISOString()
    }]
    console.log('[DataAnalysis] 使用HTML图表 - 创建虚拟配置（功能受限）')
  } else {
    currentCharts.value = []
    console.log('[DataAnalysis] 无图表数据')
  }
  
  console.log('[DataAnalysis] currentCharts更新后 - 数量:', currentCharts.value.length, '数据:', currentCharts.value)
}

const handleDialogResponse = (response: any) => {
  console.log('[DataAnalysis] 收到对话响应:', response)
  
  // 处理报告重新生成
  if (response.action_type === 'regenerate_report') {
    console.log('[DataAnalysis] 更新报告 - 文字长度:', response.new_report_text?.length, 'HTML长度:', response.new_html_charts?.length)
    
    if (reportContent.value) {
      const newContent = {
        ...reportContent.value,
        text: response.new_report_text || reportContent.value.text,
        html_charts: response.new_html_charts || reportContent.value.html_charts
      }
      
      operationStore.setReportContent(newContent)
      ElMessage.success('报告已更新')
    }
  } else if (response.action_type === 'modify_text') {
    // 文字修改模式
    console.log('[DataAnalysis] 文字修改 - 新文字长度:', response.new_report_text?.length)
    
    if (reportContent.value && response.new_report_text) {
      const newContent = {
        ...reportContent.value,
        text: response.new_report_text
      }
      
      operationStore.setReportContent(newContent)
      ElMessage.success('文字已修改')
    }
  } else if (response.action_type === 'add_content') {
    // 添加新内容到报告
    console.log('[DataAnalysis] 添加内容 - 新报告长度:', response.new_report_text?.length)
    
    if (reportContent.value && response.new_report_text) {
      const newContent = {
        ...reportContent.value,
        text: response.new_report_text
      }
      
      operationStore.setReportContent(newContent)
      ElMessage.success('新内容已添加到报告')
    }
  } else if (response.action_type === 'delete_content') {
    // 删除内容
    console.log('[DataAnalysis] 删除内容 - 新报告长度:', response.new_report_text?.length)
    console.log('[DataAnalysis] 删除内容 - 当前报告长度:', reportContent.value?.text?.length)
    console.log('[DataAnalysis] 删除内容 - new_report_text存在:', !!response.new_report_text)
    
    if (reportContent.value && response.new_report_text) {
      const newContent = {
        ...reportContent.value,
        text: response.new_report_text
      }
      
      console.log('[DataAnalysis] 删除内容 - 准备更新store, 新内容长度:', newContent.text?.length)
      operationStore.setReportContent(newContent)
      console.log('[DataAnalysis] 删除内容 - store已更新')
      ElMessage.success('已删除选中的内容')
    } else {
      console.log('[DataAnalysis] 删除内容 - 条件不满足, reportContent.value:', !!reportContent.value, 'new_report_text:', !!response.new_report_text)
    }
  } else if (response.modified_charts && response.modified_charts.length > 0) {
    // 旧的图表修改模式（兼容）
    currentCharts.value = response.modified_charts

    if (reportContent.value) {
      operationStore.setReportContent({
        ...reportContent.value,
        charts: response.modified_charts
      })
    }

    ElMessage.success('图表已更新')
  }

  // 更新对话ID
  if (response.conversation_id) {
    conversationId.value = response.conversation_id
  }
}

const handleHistoryCleared = () => {
  // 清除对话历史后的处理
  conversationId.value = ''
  ElMessage.info('对话历史已清除')
}

// ========== 图表编辑功能（新版：全屏编辑模式） ==========
// 点击图表 - 弹出确认对话框
const handleChartClick = () => {
  ElMessageBox.confirm(
    '在编辑模式中，你可以即时修改颜色、类型、样式，也可以使用AI进行复杂修改。',
    '进入图表编辑模式？',
    {
      confirmButtonText: '进入编辑',
      cancelButtonText: '取消',
      type: 'info',
      icon: markRaw(DataAnalysis)
    }
  ).then(() => {
    // 进入编辑模式
    editingChartHtml.value = reportContent.value?.html_charts || ''
    editingChartTitle.value = '数据分析图表'
    showChartEditor.value = true
    console.log('[DataAnalysis] 进入图表编辑模式')
  }).catch(() => {
    // 用户取消
  })
}

// 保存图表编辑
const handleChartEditorSave = async (newHtml: string) => {
  if (reportContent.value) {
    const newContent = {
      ...reportContent.value,
      html_charts: newHtml
    }
    
    // 只更新内容，不询问保存版本（等到退出AI编辑模式时再询问）
    operationStore.setReportContent(newContent)
    ElMessage.success('图表已更新')
    console.log('[DataAnalysis] 图表已更新（未创建版本）')
  }
}

// 取消图表编辑
const handleChartEditorCancel = () => {
  console.log('[DataAnalysis] 取消图表编辑')
}

// 退出编辑模式
const handleExitEdit = () => {
  // 直接调用toggleDialogPanel关闭对话面板
  toggleDialogPanel()
}

// ========== 文本选择监听（用于AI对话修改） ==========
const handleTextSelection = () => {
  // 只在对话面板打开时监听
  if (!showDialogPanel.value) return
  
  const selection = window.getSelection()
  const selectedText = selection?.toString().trim()
  
  if (!selectedText || selectedText.length < 2) {
    return
  }
  
  // 检查选中的文本是否在报告区域内
  const reportArea = reportDisplayRef.value
  if (!reportArea || !selection?.anchorNode) return
  
  if (!reportArea.contains(selection.anchorNode)) {
    return
  }
  
  console.log('[DataAnalysis] 检测到文本选择:', selectedText.substring(0, 50) + '...')
  
  // 添加高亮动画效果
  addSelectionHighlight(selection)
  
  // 提取上下文
  const context = extractTextContext(selectedText, reportArea)
  
  // 传递给DialogPanel
  if (dialogPanelRef.value) {
    dialogPanelRef.value.setSelectedText(selectedText, context)
  }
}

// 添加选中文字的高亮动画
const addSelectionHighlight = (selection: Selection) => {
  try {
    const range = selection.getRangeAt(0)
    
    // 创建高亮元素
    const highlight = document.createElement('span')
    highlight.className = 'text-selection-highlight'
    highlight.style.cssText = `
      background: linear-gradient(120deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.3) 100%);
      border-radius: 4px;
      padding: 2px 0;
      animation: highlightPulse 0.5s ease-out;
    `
    
    // 包裹选中的内容
    range.surroundContents(highlight)
    
    // 2秒后移除高亮效果
    setTimeout(() => {
      if (highlight.parentNode) {
        const parent = highlight.parentNode
        while (highlight.firstChild) {
          parent.insertBefore(highlight.firstChild, highlight)
        }
        parent.removeChild(highlight)
      }
    }, 2000)
  } catch (e) {
    // 如果无法包裹（跨元素选择），忽略错误
    console.log('[DataAnalysis] 无法添加高亮效果（可能是跨元素选择）')
  }
}

// 提取选中文字的上下文
const extractTextContext = (selectedText: string, container: HTMLElement) => {
  const fullText = container.innerText || ''
  const startIndex = fullText.indexOf(selectedText)
  
  if (startIndex === -1) {
    return {
      beforeContext: '',
      afterContext: '',
      fullText: fullText
    }
  }
  
  const endIndex = startIndex + selectedText.length
  const CONTEXT_LENGTH = 500
  
  return {
    beforeContext: fullText.substring(Math.max(0, startIndex - CONTEXT_LENGTH), startIndex),
    afterContext: fullText.substring(endIndex, Math.min(fullText.length, endIndex + CONTEXT_LENGTH)),
    fullText: fullText
  }
}

// ========== 拖拽调整历史会话栏宽度 ==========
const startSidebarResize = (e: MouseEvent) => {
  isSidebarResizing.value = true
  sidebarStartX.value = e.clientX
  sidebarStartWidth.value = sidebarWidth.value
  
  document.addEventListener('mousemove', handleSidebarResize)
  document.addEventListener('mouseup', stopSidebarResize)
  
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

const handleSidebarResize = (e: MouseEvent) => {
  if (!isSidebarResizing.value) return
  
  const deltaX = e.clientX - sidebarStartX.value
  const newWidth = sidebarStartWidth.value + deltaX
  
  // 限制宽度范围：200px - 400px
  if (newWidth >= 200 && newWidth <= 400) {
    sidebarWidth.value = newWidth
  }
}

const stopSidebarResize = () => {
  isSidebarResizing.value = false
  document.removeEventListener('mousemove', handleSidebarResize)
  document.removeEventListener('mouseup', stopSidebarResize)
  
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

// ========== 拖拽调整对话面板宽度 ==========
const startResize = (e: MouseEvent) => {
  isResizing.value = true
  startX.value = e.clientX
  startWidth.value = dialogPanelWidth.value
  
  document.addEventListener('mousemove', handleDialogPanelResize)
  document.addEventListener('mouseup', stopResize)
  
  // 添加拖拽时的样式
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

const handleDialogPanelResize = (e: MouseEvent) => {
  if (!isResizing.value) return
  
  const deltaX = e.clientX - startX.value
  const newWidth = startWidth.value + deltaX
  
  // 限制宽度范围：300px - 800px
  if (newWidth >= 300 && newWidth <= 800) {
    dialogPanelWidth.value = newWidth
  }
}

const stopResize = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', handleDialogPanelResize)
  document.removeEventListener('mouseup', stopResize)
  
  // 移除拖拽时的样式
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

const openSettings = () => {
  // 简化版：所有用户都可以配置工作流（或根据实际需求调整）
  fillSettingsForm()
  showSettings.value = true
}

// 监听来自批量分析页面的设置打开事件
const handleOpenSettings = () => {
  openSettings()
}

onMounted(async () => {
  window.addEventListener('open-workflow-settings', handleOpenSettings)
  
  // 添加文本选择监听
  document.addEventListener('mouseup', handleTextSelection)
  
  // 加载工作流配置
  loadFunctionWorkflow()
  
  // 检查路由参数，判断是否需要开始新会话
  const route = useRoute()
  const startNew = route.query.new === 'true'
  
  if (startNew) {
    // 从首页点击进入，清空所有状态，开始全新分析
    console.log('[DataAnalysis] 开始新的分析会话')
    operationStore.clearSession()
    localStorage.removeItem('currentSessionId')
    
    // 清空报告内容（已在 clearSession 中处理）
    fileList.value = []
    isViewingHistory.value = false
    currentVersion.value = null
    
    // 加载会话列表（但不自动选择）
    await sidebarRef.value?.loadSessions()
  } else {
    // 正常加载（页面刷新等情况）
    // 加载会话列表
    await sidebarRef.value?.loadSessions()
    
    // 如果存在当前会话ID，自动加载会话详情（包括html_charts）
    if (operationStore.currentSessionId) {
      console.log('[DataAnalysis] 页面刷新，自动加载当前会话:', operationStore.currentSessionId)
      await handleSessionSelected(operationStore.currentSessionId)
    } else {
      // 如果Store中没有会话ID，尝试从localStorage恢复最后一个会话的html_charts（临时方案）
      // 注意：这只是一个备用方案，主要依赖后端数据库
      const lastSessionId = localStorage.getItem('currentSessionId')
      if (lastSessionId) {
        const storageKey = `html_charts_${lastSessionId}`
        try {
          const savedHtmlCharts = localStorage.getItem(storageKey)
          if (savedHtmlCharts && !operationStore.reportContent?.html_charts) {
            console.log('[DataAnalysis] 从localStorage恢复最后一个会话的HTML图表（备用方案）')
            // 这里不自动加载，因为需要完整的会话数据，只作为最后的备用
          }
        } catch (e) {
          console.warn('[DataAnalysis] 从localStorage读取失败:', e)
        }
      }
    }
  }
  
  // 初始化图表容器
  nextTick(() => {
    renderCharts([])
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('open-workflow-settings', handleOpenSettings)
  document.removeEventListener('mouseup', handleTextSelection)
})

// 保存工作流配置（用户级配置）
const saveWorkflowConfig = async () => {
  if (!canSaveWorkflow.value) return

  saving.value = true
  try {
    // 将用户配置转换为工作流配置格式
    const config = {
      api_key: settingsForm.value.config.api_key,
      api_url: settingsForm.value.config.url_file?.replace('/files/upload', '').replace('/chat-messages', '') || '',
      url_file: settingsForm.value.config.url_file,
      url_work: settingsForm.value.config.url_work,
      workflow_id: '1', // 固定为1，实际使用url_work
      workflow_type: 'chatflow', // 固定为chatflow
      file_param: settingsForm.value.config.file_param || 'excell',
      query_param: settingsForm.value.config.query_param || 'query',
      input_field: `${settingsForm.value.config.file_param || 'excell'},${settingsForm.value.config.query_param || 'query'}`
    }

    const workflowData = {
      name: '运营数据分析工作流',
      category: 'operation',
      platform: 'dify',
      description: '用户配置的工作流',
      config: config,
      is_active: true
    }

    let workflowId: number

    if (currentWorkflow.value) {
      // 更新现有工作流
      const updateRes = await updateWorkflow(currentWorkflow.value.id, workflowData) as unknown as ApiResponse<any>
      
      if (!updateRes.success || !updateRes.data) {
        throw new Error('更新工作流失败')
      }
      
      workflowId = updateRes.data.id
      ElMessage.success('工作流配置已更新')
    } else {
      // 创建新工作流
      const createRes = await createWorkflow(workflowData) as unknown as ApiResponse<any>
      
      if (!createRes.success || !createRes.data) {
        throw new Error('创建工作流失败')
      }

      workflowId = createRes.data.id

      // 绑定工作流到当前功能（用户级绑定）
      await bindFunctionWorkflow({
        function_key: 'operation_data_analysis',
        workflow_id: workflowId
      })

      ElMessage.success('工作流配置成功')
    }

    showSettings.value = false
    
    // 重新加载配置
    await loadFunctionWorkflow()
  } catch (error: any) {
    console.error('保存工作流配置失败:', error)
    ElMessage.error(error.message || '保存工作流配置失败')
  } finally {
    saving.value = false
  }
}

// 文件处理
const validateFile = (file: File): boolean => {
  const validTypes = ['.xlsx', '.csv']
  const maxSize = 10 * 1024 * 1024 // 10MB
  
  const ext = file.name.substring(file.name.lastIndexOf('.'))
  if (!validTypes.includes(ext.toLowerCase())) {
    ElMessage.error('只支持 .xlsx 和 .csv 格式的文件')
    return false
  }
  
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过10MB')
    return false
  }
  
  return true
}

const handleFileChange = async (file: UploadFile) => {
  if (!file.raw) return
  
  // 验证文件格式和大小
  if (!validateFile(file.raw)) {
    uploadRef.value?.clearFiles()
    return
  }
  
  try {
    // 如果没有会话，先创建一个新会话
    let sessionId = operationStore.currentSessionId
    if (!sessionId) {
      ElMessage.info('正在创建新会话...')
      try {
        const createResponse = await createSession() as unknown as ApiResponse<Session>  // 移除project_id参数
        if (createResponse.success && createResponse.data) {
          const newSession = createResponse.data
          operationStore.addSession(newSession)
          operationStore.setCurrentSession(newSession.id)
          sessionId = newSession.id
          // 通知侧边栏刷新
          sidebarRef.value?.loadSessions()
          ElMessage.success('新会话已创建')
        } else {
          console.error('创建会话响应格式错误:', createResponse)
          ElMessage.error('创建会话失败，请重试')
          uploadRef.value?.clearFiles()
          return
        }
      } catch (error: any) {
        console.error('创建会话失败:', error)
        ElMessage.error(error.message || '创建会话失败，请重试')
        uploadRef.value?.clearFiles()
        return
      }
    }
    
    // 开始上传文件
    uploadProgress.value = 0
    ElMessage.info('正在上传文件...')
    
    if (!sessionId) {
      ElMessage.error('会话ID不存在，请先创建会话')
      return
    }
    
    const response = await uploadExcel(
      file.raw,
      sessionId,
      (progress) => {
        uploadProgress.value = progress
      }
    )
    
    const uploadResponse = response as unknown as ApiResponse<UploadResponse>
    if (uploadResponse.success && uploadResponse.data) {
      operationStore.setFileId(uploadResponse.data.file_id)
      operationStore.setCurrentFile(file.raw)
      ElMessage.success(`文件上传成功: ${file.name}`)
      uploadProgress.value = 100
      
      // 更新文件列表显示
      fileList.value = [{
        name: file.name,
        status: 'success',
        uid: file.uid,
        raw: file.raw
      }]
      
      // 刷新历史会话列表，确保新创建的会话显示在历史记录中
      sidebarRef.value?.loadSessions()
    } else {
      console.error('文件上传响应格式错误:', response)
      const errorResponse = response as unknown as ApiResponse<any>
      ElMessage.error(errorResponse.message || '文件上传失败')
      uploadRef.value?.clearFiles()
      uploadProgress.value = 0
    }
  } catch (error: any) {
    console.error('文件上传错误:', error)
    const errorMsg = error.response?.data?.error?.message || error.message || '文件上传失败'
    ElMessage.error(errorMsg)
    uploadRef.value?.clearFiles()
    uploadProgress.value = 0
  }
}

const handleFileRemove = () => {
  operationStore.setFileId(null)
  operationStore.setCurrentFile(null)
  uploadProgress.value = 0
  fileList.value = []
}

const handleUploadError = (error: Error, file: UploadFile) => {
  console.error('文件上传错误:', error, file)
  ElMessage.error(`文件上传失败: ${error.message || '未知错误'}`)
  uploadRef.value?.clearFiles()
  uploadProgress.value = 0
}

const triggerFileSelect = () => {
  const input = uploadRef.value?.$el?.querySelector('input[type="file"]')
  if (input) {
    input.click()
  } else {
    ElMessage.warning('无法打开文件选择器，请直接拖拽文件')
  }
}

// 分析需求提交（简化版，移除project_id参数）
const submitAnalysis = async () => {
  if (!canSubmit.value) {
    ElMessage.warning('请先上传Excel文件并输入分析需求')
    return
  }
  
  if (!operationStore.currentSessionId || !operationStore.fileId) {
    ElMessage.warning('请先创建会话并上传文件')
    return
  }
  
  // 检查工作流配置
  if (!currentWorkflow.value) {
    ElMessage.warning({
      message: '尚未配置工作流，请先配置工作流后再进行分析',
      duration: 5000,
      showClose: true
    })
    // 自动打开配置对话框
    openSettings()
    return
  }
  
  operationStore.setGenerating(true)
  
  try {
    const response = await generateReport({
      session_id: operationStore.currentSessionId,
      file_id: operationStore.fileId,
      analysis_request: analysisRequest.value,
      chart_customization_prompt: enableChartCustomization.value ? chartCustomizationPrompt.value : undefined,
      chart_generation_mode: "html"  // 使用HTML模式
    })
    
    const reportResponse = response as unknown as ApiResponse<ReportResponse>
    if (reportResponse.success && reportResponse.data) {
      const reportData = reportResponse.data
      
      // 使用日志系统记录所有数据
      frontendLogger.log('报告生成', '接收到的API响应', {
        reportId: reportData.report_id,
        hasContent: !!reportData.content,
        contentKeys: reportData.content ? Object.keys(reportData.content) : [],
        textExists: !!reportData.content?.text,
        textLength: reportData.content?.text?.length,
        textPreview: reportData.content?.text?.substring(0, 200),
        chartsCount: reportData.content?.charts?.length || 0,
        htmlChartsExists: !!reportData.content?.html_charts,
        htmlChartsLength: reportData.content?.html_charts?.length || 0,
        htmlChartsPreview: reportData.content?.html_charts?.substring(0, 200) || '空',
        chartsPreview: reportData.content?.charts?.map((c: any) => ({
          type: c.type,
          hasConfig: !!c.config,
          title: c.title
        }))
      })
      
      // 设置报告内容
      frontendLogger.log('报告生成', '准备设置 reportContent', {
        content: reportData.content,
        textType: typeof reportData.content?.text,
        textIsString: typeof reportData.content?.text === 'string',
        textLength: reportData.content?.text?.length || 0
      })
      
      operationStore.setReportContent(reportData.content)
      
      // 三重保障：同时保存到localStorage和sessionStorage（防止刷新后丢失）
      if (reportData.content?.html_charts) {
        const storageKey = `html_charts_${operationStore.currentSessionId}`
        try {
          // 保存到localStorage（长期存储）
          localStorage.setItem(storageKey, reportData.content.html_charts)
          // 保存到sessionStorage（会话级存储，更可靠）
          sessionStorage.setItem(storageKey, reportData.content.html_charts)
          // 保存当前会话ID
          localStorage.setItem('currentSessionId', String(operationStore.currentSessionId))
          console.log('[DataAnalysis] HTML图表已保存到localStorage和sessionStorage:', storageKey, '长度:', reportData.content.html_charts.length)
        } catch (e) {
          console.warn('[DataAnalysis] 保存到Storage失败:', e)
        }
      }
      
      frontendLogger.log('报告生成', '已设置 reportContent 到 store', {
        storeTextExists: !!operationStore.reportContent?.text,
        storeTextType: typeof operationStore.reportContent?.text,
        storeTextLength: operationStore.reportContent?.text?.length,
        storeChartsCount: operationStore.reportContent?.charts?.length || 0,
        storeHtmlChartsExists: !!operationStore.reportContent?.html_charts,
        storeHtmlChartsLength: operationStore.reportContent?.html_charts?.length || 0,
        storeHtmlChartsPreview: operationStore.reportContent?.html_charts?.substring(0, 200) || '空'
      })
      
      operationStore.setReportId(String(reportData.report_id))
      
      // 等待一下，确保 watch 触发
      await nextTick()
      await nextTick()
      await nextTick() // 多等一次，确保 watch 完成
      
      // 渲染图表
      renderCharts(reportData.content.charts || [])
      
      ElMessage.success('报告生成成功')
    }
  } catch (error: any) {
    console.error('报告生成失败:', error)
    
    let errorMsg = '报告生成失败，请重试'
    let isDifyError = false
    
    if (error.response?.data) {
      const data = error.response.data
      errorMsg = data.detail || data.error?.message || data.message || errorMsg
    } else if (error.message) {
      errorMsg = error.message
    }
    
    // 检查是否是 Dify 相关错误
    const difyKeywords = ['dify', '工作流', 'workflow', 'api key', 'api_key', '未配置', '不存在', '已禁用']
    isDifyError = difyKeywords.some(keyword => 
      errorMsg.toLowerCase().includes(keyword.toLowerCase())
    )
    
    // 使用 ElNotification 显示更详细的错误信息
    if (isDifyError) {
      ElNotification({
        title: '工作流执行失败',
        message: errorMsg,
        type: 'error',
        duration: 8000,
        showClose: true,
        dangerouslyUseHTMLString: true,
        onClick: () => {
          // 点击通知时打开配置对话框
          openSettings()
        }
      })
      
      // 同时显示帮助信息
      setTimeout(() => {
        ElNotification({
          title: '故障排查建议',
          message: `
            <div style="line-height: 1.6;">
              <p style="margin: 4px 0;"><strong>请检查以下配置：</strong></p>
              <p style="margin: 4px 0;">1. Dify API 地址和 API Key 是否正确</p>
              <p style="margin: 4px 0;">2. Dify Chatflow 是否配置正确</p>
              <p style="margin: 4px 0;">3. 文件是否成功上传到 Dify</p>
              <p style="margin: 4px 0;">4. 工作流是否已启用</p>
              <p style="margin-top: 8px; color: #409EFF; cursor: pointer;">
                <strong>点击此处打开工作流配置</strong>
              </p>
            </div>
          `,
          type: 'warning',
          duration: 10000,
          showClose: true,
          dangerouslyUseHTMLString: true,
          onClick: () => {
            openSettings()
          }
        })
      }, 500) // 延迟500ms显示，避免与错误通知重叠
    } else {
      ElMessage.error({
        message: errorMsg,
        duration: 5000,
        showClose: true
      })
    }
  } finally {
    operationStore.setGenerating(false)
  }
}

// 图表尺寸自适应调整工具函数
interface ContentSize {
  scrollWidth: number
  scrollHeight: number
  clientWidth: number
  clientHeight: number
  chartSize?: {
    width: number
    height: number
    aspectRatio: number
  }
}

interface ScreenSize {
  width: number
  height: number
  isMobile: boolean
  isTablet: boolean
  isDesktop: boolean
}

// 检测内容尺寸
const detectContentSize = (iframe: HTMLIFrameElement): ContentSize | null => {
  try {
    const doc = iframe.contentDocument || iframe.contentWindow?.document
    if (!doc) return null
    
    const body = doc.body
    const html = doc.documentElement
    
    // 检测图表容器（ECharts、Chart.js等）
    const chartSelectors = [
      'canvas',
      '#chart',
      '.chart',
      '[id*="chart"]',
      '[class*="chart"]'
    ]
    
    let chartSize = null
    for (const selector of chartSelectors) {
      const element = doc.querySelector(selector) as HTMLElement | null
      if (element) {
        chartSize = {
          width: element.offsetWidth || element.clientWidth,
          height: element.offsetHeight || element.clientHeight,
          aspectRatio: (element.offsetWidth || 1) / (element.offsetHeight || 1)
        }
        break
      }
    }
    
    return {
      scrollWidth: Math.max(body.scrollWidth, html.scrollWidth),
      scrollHeight: Math.max(body.scrollHeight, html.scrollHeight),
      clientWidth: Math.max(body.clientWidth, html.clientWidth),
      clientHeight: Math.max(body.clientHeight, html.clientHeight),
      chartSize: chartSize || undefined
    }
  } catch (e) {
    return null
  }
}

// 获取屏幕尺寸
const getScreenSize = (): ScreenSize => {
  const width = window.innerWidth
  return {
    width,
    height: window.innerHeight,
    isMobile: width < 768,
    isTablet: width >= 768 && width < 1024,
    isDesktop: width >= 1024
  }
}

// 获取尺寸参数（根据屏幕尺寸）
const getSizeParams = (screenSize: ScreenSize) => {
  if (screenSize.isMobile) {
    return { minHeight: 400, maxHeight: 800, defaultHeight: 500 }
  } else if (screenSize.isTablet) {
    return { minHeight: 500, maxHeight: 1000, defaultHeight: 600 }
  } else {
    return { minHeight: 600, maxHeight: 1200, defaultHeight: 700 }
  }
}

// 计算最优高度
const calculateOptimalHeight = (
  contentSize: ContentSize,
  containerWidth: number,
  sizeParams: ReturnType<typeof getSizeParams>
): number => {
  let height = contentSize.scrollHeight
  
  // 如果检测到图表容器，优先使用图表高度
  if (contentSize.chartSize) {
    const chartHeight = contentSize.chartSize.height
    // 图表高度 + 其他内容（标题、按钮等）的预估高度
    height = chartHeight + 100
  }
  
  // 根据宽高比调整（如果内容宽度超过容器，可能需要更多高度）
  if (contentSize.scrollWidth > containerWidth) {
    const aspectRatio = contentSize.scrollWidth / containerWidth
    if (aspectRatio > 1.5) {
      // 内容宽度是容器的1.5倍以上，增加高度避免过度压缩
      height = Math.max(height, containerWidth * 0.7) // 保持0.7的宽高比
    }
  }
  
  // 应用最小和最大高度限制
  height = Math.max(sizeParams.minHeight, Math.min(sizeParams.maxHeight, height))
  
  return Math.ceil(height)
}

// 调整iframe尺寸
const adjustIframeSize = (iframe: HTMLIFrameElement) => {
  const contentSize = detectContentSize(iframe)
  if (!contentSize) {
    // 跨域限制，使用默认高度
    const screenSize = getScreenSize()
    const sizeParams = getSizeParams(screenSize)
    iframe.style.height = `${sizeParams.defaultHeight}px`
    console.log('[图表尺寸] 跨域限制，使用默认高度:', sizeParams.defaultHeight)
    return
  }
  
  const containerWidth = iframe.offsetWidth || iframe.parentElement?.offsetWidth || 800
  const screenSize = getScreenSize()
  const sizeParams = getSizeParams(screenSize)
  
  const optimalHeight = calculateOptimalHeight(contentSize, containerWidth, sizeParams)
  iframe.style.height = `${optimalHeight}px`
  
  console.log('[图表尺寸] 已调整:', {
    contentSize: {
      width: contentSize.scrollWidth,
      height: contentSize.scrollHeight
    },
    chartSize: contentSize.chartSize,
    optimalHeight,
    containerWidth,
    screenSize: screenSize.isMobile ? 'mobile' : screenSize.isTablet ? 'tablet' : 'desktop'
  })
}

// 防抖函数
const debounce = <T extends (...args: any[]) => void>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout | null = null
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

let adjustTimeout: NodeJS.Timeout | null = null

// iframe加载完成处理（智能自适应调整）
// 注意：此函数目前未使用，保留用于预览功能（可选）
// @ts-ignore - 保留用于预览功能
const handleHtmlChartLoad = (_event: Event) => {
  const iframe = _event.target as HTMLIFrameElement
  console.log('[HTML图表] iframe加载完成，开始智能调整尺寸')
  
  // 首次调整（等待内容渲染）
  setTimeout(() => {
    adjustIframeSize(iframe)
  }, 300) // 等待图表完全渲染
  
  // 监听内容变化（如图表动画、数据更新等）
  try {
    const doc = iframe.contentDocument || iframe.contentWindow?.document
    if (doc) {
      // 使用MutationObserver监听DOM变化
      const observer = new MutationObserver(() => {
        clearTimeout(adjustTimeout!)
        adjustTimeout = setTimeout(() => adjustIframeSize(iframe), 300)
      })
      
      observer.observe(doc.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style', 'class']
      })
      
      // 保存observer到iframe的dataset，以便后续清理
      ;(iframe as any)._sizeObserver = observer
    }
  } catch (e) {
    console.warn('[HTML图表] 无法监听内容变化（可能跨域）:', e)
  }
}

// 窗口大小变化监听（响应式调整）
const handleResize = debounce(() => {
  const iframes = document.querySelectorAll('.html-charts-iframe')
  iframes.forEach(iframe => {
    if (iframe instanceof HTMLIFrameElement) {
      adjustIframeSize(iframe)
    }
  })
}, 300)

// 组件挂载时添加resize监听
onMounted(() => {
  window.addEventListener('resize', handleResize)
})

// 组件卸载时清理
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  // 清理所有iframe的observer
  const iframes = document.querySelectorAll('.html-charts-iframe')
  iframes.forEach(iframe => {
    if (iframe instanceof HTMLIFrameElement && (iframe as any)._sizeObserver) {
      ;(iframe as any)._sizeObserver.disconnect()
    }
  })
})

// 监听html_charts变化，确保iframe正确渲染
watch(() => reportContent.value?.html_charts, (newHtml) => {
  if (newHtml) {
    console.log('[HTML图表] 检测到新的HTML内容，长度:', newHtml.length)
    nextTick(() => {
      // iframe会自动通过:srcdoc绑定更新
    })
  }
}, { immediate: true })

// 渲染图表（降级方案：如果没有html_charts，使用ECharts）
const renderCharts = async (charts: any[]) => {
  // 如果已经有html_charts，不渲染ECharts
  if (reportContent.value?.html_charts) {
    console.log('[图表渲染] 使用HTML模式，跳过ECharts渲染')
    return
  }
  
  if (!charts || charts.length === 0) return
  
  await nextTick()
  
  charts.forEach((chart, index) => {
    const chartElement = document.getElementById(`chart-${index}`)
    if (!chartElement) return
    
    // 如果已存在实例，先销毁
    const existingInstance = chartInstances.value.get(index)
    if (existingInstance) {
      existingInstance.dispose()
    }
    
    const chartInstance = echarts.init(chartElement)
    chartInstances.value.set(index, chartInstance)
    
    // 设置图表配置
    const option = chart.config || {
      title: {
        text: chart.title || '图表'
      },
      tooltip: {},
      xAxis: {
        type: 'category',
        data: chart.data?.xAxis || []
      },
      yAxis: {
        type: 'value'
      },
      series: [{
        type: chart.type || 'line',
        data: chart.data?.series || []
      }]
    }
    
    chartInstance.setOption(option)
    
    // 响应式调整
    window.addEventListener('resize', () => {
      chartInstance.resize()
    })
  })
}

const setChartRef = (_el: any, _index: number) => {
  // 图表容器引用已通过ID设置
}



// 导出图表为Base64图片数组
const exportChartsAsImages = async () => {
  const chartImages: Array<{index: number, title: string, image: string}> = []
  
  // 遍历所有图表实例
  for (const [index, chartInstance] of chartInstances.value.entries()) {
    try {
      const imageDataUrl = chartInstance.getDataURL({
        type: 'png',
        pixelRatio: 2,
        backgroundColor: '#fff'
      })
      
      const chartData = reportContent.value?.charts?.[index] as any
      const chartTitle = chartData?.title || 
                        chartData?.config?.title?.text ||
                        `图表${index + 1}`
      
      chartImages.push({
        index: index,
        title: chartTitle,
        image: imageDataUrl
      })
    } catch (error) {
      console.error(`导出图表${index}失败:`, error)
    }
  }
  
  return chartImages
}

// 下载报告（简化版，移除project_id参数）
// 打开图表抽屉
const openChartDrawer = () => {
  if (reportContent.value?.html_charts) {
    showChartDrawer.value = true
  } else {
    ElMessage.warning('暂无图表内容')
  }
}

// 关闭图表抽屉
const handleChartDrawerClose = () => {
  showChartDrawer.value = false
}

// 下载图表
const downloadChart = async () => {
  if (!reportContent.value?.html_charts) {
    ElMessage.warning('暂无图表内容')
    return
  }

  try {
    // 导出HTML文件
    const htmlContent = reportContent.value.html_charts
    const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 生成文件名（包含时间戳）
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
    link.download = `图表_${timestamp}.html`
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    ElMessage.success('图表已保存为HTML文件')
  } catch (error) {
    console.error('下载图表失败:', error)
    ElMessage.error('下载图表失败，请稍候再试')
  }
}

const downloadReport = async () => {
  if (!operationStore.currentSessionId) {
    ElMessage.warning('会话ID不存在，请先创建会话并生成报告')
    return
  }
  
  if (!operationStore.reportContent) {
    ElMessage.warning('报告内容不存在，请先生成报告')
    return
  }
  
  try {
    ElMessage.info('正在准备下载，请稍候...')
    
    let chartImages: Array<{index: number, title: string, image: string}> = []
    
    // 1. 导出图表为图片
    if (reportContent.value?.html_charts) {
      // 如果有 HTML 图表，使用 html2canvas 截图
      try {
        ElMessage.info('正在截图HTML图表，请稍候...')
        const html2canvas = (await import('html2canvas')).default
        
        // 创建一个iframe来渲染HTML图表（确保脚本正确执行）
        const tempIframe = document.createElement('iframe')
        tempIframe.style.position = 'absolute'
        tempIframe.style.left = '-9999px'
        tempIframe.style.top = '0'
        tempIframe.style.width = '1200px'
        tempIframe.style.height = '800px'
        tempIframe.style.border = 'none'
        tempIframe.sandbox.add('allow-scripts', 'allow-same-origin')
        document.body.appendChild(tempIframe)
        
        // 等待iframe加载
        await new Promise<void>((resolve) => {
          tempIframe.onload = () => resolve()
          tempIframe.srcdoc = reportContent.value!.html_charts!
        })
        
        // 等待iframe内容完全加载
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        // 获取iframe内容
        let targetElement: HTMLElement | null = null
        try {
          const iframeDoc = tempIframe.contentDocument || tempIframe.contentWindow?.document
          if (iframeDoc && iframeDoc.body) {
            targetElement = iframeDoc.body
            
            // 等待图表渲染完成（检查canvas元素或图表容器）
            let attempts = 0
            const maxAttempts = 20 // 最多等待10秒
            
            while (attempts < maxAttempts) {
              // 检查是否有canvas元素（ECharts等图表库会创建canvas）
              const canvases = targetElement.querySelectorAll('canvas')
              
              // 如果找到canvas或者等待时间足够长，认为图表已渲染
              if (canvases.length > 0 || attempts >= 10) {
                // 再等待一下确保图表完全绘制
                await new Promise(resolve => setTimeout(resolve, 1000))
                break
              }
              
              await new Promise(resolve => setTimeout(resolve, 500))
              attempts++
            }
            
            // 等待所有图片加载完成
            const images = targetElement.querySelectorAll('img')
            if (images.length > 0) {
              await Promise.all(
                Array.from(images).map((img: HTMLImageElement) => {
                  if (img.complete) {
                    return Promise.resolve(undefined)
                  }
                  return new Promise<void>((resolve) => {
                    img.onload = () => resolve()
                    img.onerror = () => resolve() // 即使失败也继续
                    setTimeout(() => resolve(), 3000) // 超时也继续
                  })
                })
              )
            }
            
            // 最后等待一下，确保所有内容都渲染完成
            await new Promise(resolve => setTimeout(resolve, 1000))
          }
        } catch (e) {
          console.warn('无法访问iframe内容，尝试截图iframe本身:', e)
          targetElement = tempIframe
        }
        
        if (!targetElement) {
          throw new Error('无法获取图表内容')
        }
        
        // 截图
        const canvas = await html2canvas(targetElement, {
          backgroundColor: '#ffffff',
          scale: 2,
          useCORS: true,
          logging: false,
          allowTaint: true,
          width: targetElement.scrollWidth || 1200,
          height: targetElement.scrollHeight || 800,
          windowWidth: targetElement.scrollWidth || 1200,
          windowHeight: targetElement.scrollHeight || 800
        })
        
        // 转换为 base64
        const imageDataUrl = canvas.toDataURL('image/png', 1.0)
        
        if (!imageDataUrl || imageDataUrl === 'data:,') {
          throw new Error('截图生成失败：图片数据为空')
        }
        
        chartImages.push({
          index: 0,
          title: '数据可视化图表',
          image: imageDataUrl
        })
        
        // 清理临时元素
        document.body.removeChild(tempIframe)
        ElMessage.success('图表截图成功')
      } catch (error) {
        console.error('HTML图表截图失败:', error)
        ElMessage.warning(`图表截图失败: ${error instanceof Error ? error.message : '未知错误'}，将生成不含图表的PDF`)
      }
    } else if (chartInstances.value.size > 0) {
      // 如果有 ECharts 实例，使用原有方法
      await new Promise(resolve => setTimeout(resolve, 1000))
      chartImages = await exportChartsAsImages()
    }
    
    // 2. 调用后端API，传递图表图片（移除project_id参数）
    const reportId = operationStore.reportId || `report_${operationStore.currentSessionId}`
    const response = await downloadReportPDF(
      reportId,
      operationStore.currentSessionId,
      chartImages
    )
    
    // 检查响应是否是 Blob（对于 Blob 响应，拦截器返回原始 AxiosResponse）
    const axiosResponse = response as any as AxiosResponse
    if (axiosResponse.data instanceof Blob) {
      const contentType = axiosResponse.headers?.['content-type'] || ''
      if (contentType.includes('application/json')) {
        const text = await axiosResponse.data.text()
        try {
          const jsonData = JSON.parse(text)
          const errorMsg = jsonData?.error?.message || jsonData?.detail || jsonData?.message || '报告下载失败'
          ElMessage.error(errorMsg)
          return
        } catch {
          ElMessage.error('报告下载失败')
          return
        }
      }
      
      // 是 PDF 文件，创建下载链接
      const blob = new Blob([axiosResponse.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      const sessionTitle = operationStore.currentSession?.title || '数据分析报告'
      link.download = `${sessionTitle}_${new Date().getTime()}.pdf`
      link.click()
      window.URL.revokeObjectURL(url)
      ElMessage.success('报告下载成功')
    } else {
      ElMessage.error('响应格式错误')
    }
  } catch (error: any) {
    console.error('下载报告失败:', error)
    if (error.response?.data instanceof Blob) {
      try {
        const text = await error.response.data.text()
        const jsonData = JSON.parse(text)
        const errorMsg = jsonData?.error?.message || jsonData?.detail || jsonData?.message || '报告下载失败'
        ElMessage.error(errorMsg)
      } catch {
        ElMessage.error('报告下载失败')
      }
    } else {
      const errorMsg = error.response?.data?.detail || error.message || '报告下载失败'
      ElMessage.error(errorMsg)
    }
  }
}


// 使用示例
const useExample = (example: string) => {
  analysisRequest.value = example
}

// 会话选择处理
const handleSessionSelected = async (sessionId: number) => {
  try {
    console.log('🔵🔵🔵 [DataAnalysis] 开始加载会话详情:', sessionId)
    
    // 关闭AI对话面板，强制进入只读查看模式
    showDialogPanel.value = false
    
    const response = await getSessionDetail(sessionId) as unknown as ApiResponse<Session>
    console.log('🔵🔵🔵 [DataAnalysis] API响应:', response)
    if (response.success && response.data) {
      const session = response.data
      console.log('🔵🔵🔵 [DataAnalysis] 会话详情加载成功:', {
        sessionId: session.id,
        messagesCount: session.messages?.length || 0,
        messages: session.messages
      })
      
      // 加载历史消息
      if (session.messages && session.messages.length > 0) {
        const userMessages = session.messages.filter((msg: any) => msg.role === 'user')
        const lastUserMsg = userMessages.length > 0 ? userMessages[userMessages.length - 1] : null
        
        if (lastUserMsg?.file_name) {
          fileList.value = [{
            name: lastUserMsg.file_name,
            status: 'success'
          } as UploadFile]
          ElMessage.info(`已加载历史会话：${session.title}`)
        }
        
        const assistantMessages = session.messages.filter((msg: any) => msg.role === 'assistant')
        const lastAssistantMsg = assistantMessages.length > 0 ? assistantMessages[assistantMessages.length - 1] : null
        
        console.log('🔵🔵🔵 [DataAnalysis] 最后一条assistant消息:', {
          hasMessage: !!lastAssistantMsg,
          hasContent: !!lastAssistantMsg?.content,
          hasCharts: !!lastAssistantMsg?.charts,
          hasHtmlCharts: !!lastAssistantMsg?.html_charts,
          htmlChartsLength: lastAssistantMsg?.html_charts?.length || 0,
          htmlChartsPreview: lastAssistantMsg?.html_charts?.substring(0, 200) || '空'
        })
        console.log('🔵🔵🔵 [DataAnalysis] lastAssistantMsg完整对象:', lastAssistantMsg)
        
        if (lastAssistantMsg) {
          // 三重保障：优先使用后端返回的html_charts，如果没有则从sessionStorage或localStorage加载
          let htmlCharts = lastAssistantMsg.html_charts
          if (!htmlCharts) {
            const storageKey = `html_charts_${sessionId}`
            try {
              // 优先从sessionStorage恢复（更可靠）
              let savedHtmlCharts = sessionStorage.getItem(storageKey)
              if (!savedHtmlCharts) {
                // 如果sessionStorage没有，尝试localStorage
                savedHtmlCharts = localStorage.getItem(storageKey)
              }
              if (savedHtmlCharts) {
                htmlCharts = savedHtmlCharts
                console.log('[DataAnalysis] 从Storage恢复HTML图表:', storageKey, '长度:', htmlCharts.length, '来源:', sessionStorage.getItem(storageKey) ? 'sessionStorage' : 'localStorage')
              } else {
                console.warn('[DataAnalysis] Storage中没有找到HTML图表数据:', storageKey)
              }
            } catch (e) {
              console.warn('[DataAnalysis] 从Storage读取失败:', e)
            }
          } else {
            console.log('[DataAnalysis] 从后端数据库恢复HTML图表，长度:', htmlCharts.length)
          }
          
          const reportContent = {
            text: lastAssistantMsg.content || '',
            charts: lastAssistantMsg.charts || [],
            html_charts: htmlCharts || undefined,  // 加载历史会话时也包含html_charts（后端或localStorage）
            tables: lastAssistantMsg.tables || [],
            metrics: {}
          }
          
          console.log('🔵🔵🔵 [DataAnalysis] 准备设置reportContent:', {
            hasText: !!reportContent.text,
            textLength: reportContent.text.length,
            chartsCount: reportContent.charts.length,
            hasHtmlCharts: !!reportContent.html_charts,
            htmlChartsLength: reportContent.html_charts?.length || 0,
            htmlChartsSource: lastAssistantMsg.html_charts ? 'backend' : (htmlCharts ? 'localStorage' : 'none'),
            htmlChartsPreview: reportContent.html_charts?.substring(0, 200) || '空'
          })
          console.log('🔵🔵🔵 [DataAnalysis] reportContent完整对象:', reportContent)
          
          // 强制设置到store
          console.log('🔵🔵🔵 [DataAnalysis] 调用setReportContent...')
          operationStore.setReportContent(reportContent)
          console.log('🔵🔵🔵 [DataAnalysis] setReportContent调用完成')
          
          // 立即验证store中的值
          console.log('[DataAnalysis] 设置后立即验证store:', {
            storeReportContent: operationStore.reportContent,
            storeHasHtmlCharts: !!operationStore.reportContent?.html_charts,
            storeHtmlChartsLength: operationStore.reportContent?.html_charts?.length || 0,
            storeHtmlChartsType: typeof operationStore.reportContent?.html_charts
          })
          
          // 如果从localStorage恢复，也保存到后端（下次优先使用后端）
          if (htmlCharts && !lastAssistantMsg.html_charts) {
            console.log('[DataAnalysis] 从localStorage恢复的HTML图表，建议重新生成报告以保存到后端')
          }
          
          if (session.report_id) {
            operationStore.setReportId(String(session.report_id))
          }
          
          await nextTick()
          renderCharts(lastAssistantMsg.charts || [])
          
          console.log('[DataAnalysis] 历史会话加载完成，检查store中的html_charts:', {
            storeHasHtmlCharts: !!operationStore.reportContent?.html_charts,
            storeHtmlChartsLength: operationStore.reportContent?.html_charts?.length || 0
          })
          
          // 如果有报告内容，切换到查看历史报告模式
          isViewingHistory.value = true
          
          ElMessage.success('历史会话已加载')
        } else {
          // 没有报告内容，切换到新建分析模式
          isViewingHistory.value = false
          operationStore.setReportContent(null)
          operationStore.setReportId(null)
        }
      } else {
        // 没有消息，切换到新建分析模式
        isViewingHistory.value = false
        fileList.value = []
        operationStore.setReportContent(null)
        operationStore.setReportId(null)
        analysisRequest.value = ''
      }
    }
  } catch (error: any) {
    console.error('加载会话详情失败:', error)
    ElMessage.error('加载会话详情失败')
  }
}

// 会话创建处理
const handleSessionCreated = (session: any) => {
  // 重置状态（清空文件上传和报告内容）
  isViewingHistory.value = false  // 切换到新建分析模式
  fileList.value = []
  uploadProgress.value = 0
  operationStore.setFileId(null)
  operationStore.setCurrentFile(null)
  operationStore.setReportContent(null)
  operationStore.setReportId(null)
  analysisRequest.value = ''
  
  // 清除旧会话的localStorage数据（如果有）
  if (operationStore.currentSessionId) {
    const oldStorageKey = `html_charts_${operationStore.currentSessionId}`
    try {
      localStorage.removeItem(oldStorageKey)
      console.log('[DataAnalysis] 已清除旧会话的localStorage:', oldStorageKey)
    } catch (e) {
      console.warn('[DataAnalysis] 清除localStorage失败:', e)
    }
  }
  
  // 注意：不需要重新加载会话列表，因为HistorySidebar已经处理了
  // 只需要确保当前会话已设置
  if (session && session.id) {
    operationStore.setCurrentSession(session.id)
  }
}

// 版本切换处理
const handleVersionSelected = (payload: { sessionId: number; version: SessionVersionDetail }) => {
  const { sessionId, version } = payload
  console.log('[DataAnalysis] 切换版本:', version)

  operationStore.setCurrentSession(sessionId)
  currentSessionId.value = sessionId
  isViewingHistory.value = true
  currentVersion.value = version

  // 更新报告内容
  const newContent = {
    text: version.report_text || '',
    html_charts: version.report_html_charts || '',
    charts: version.report_charts_json || []
  }
  operationStore.setReportContent(newContent as any)
  updateCurrentCharts()

  // 清空当前对话ID，避免上下文错乱
  conversationId.value = ''
}

// 格式化版本时间
const formatVersionTime = (time: string) => {
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (minutes < 1) {
    return '刚刚'
  } else if (minutes < 60) {
    return `${minutes}分钟前`
  } else if (hours < 24) {
    return `${hours}小时前`
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN', { 
      year: 'numeric',
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
}

// 返回当前版本
const returnToCurrentVersion = async () => {
  if (!currentSessionId.value) {
    ElMessage.warning('未选择会话')
    return
  }

  try {
    // 重新加载会话详情，获取最新的报告内容
    const response = await getSessionDetail(currentSessionId.value)
    const sessionResponse = response as unknown as ApiResponse<Session>
    
    if (sessionResponse.success && sessionResponse.data) {
      const session = sessionResponse.data
      
      // 从最后一条消息中获取报告内容
      const lastMessage = session.messages?.[session.messages.length - 1]
      if (lastMessage) {
        const newContent = {
          text: lastMessage.content || '',
          html_charts: lastMessage.html_charts || '',
          charts: lastMessage.charts || []
        }
        operationStore.setReportContent(newContent as any)
        updateCurrentCharts()
      }
      
      // 退出历史查看模式
      isViewingHistory.value = false
      currentVersion.value = null
      
      ElMessage.success('已返回当前版本')
    } else {
      ElMessage.error(sessionResponse.message || '加载当前版本失败')
    }
  } catch (error: any) {
    console.error('返回当前版本失败:', error)
    ElMessage.error(error.response?.data?.detail || '返回当前版本失败')
  }
}
</script>

<style scoped>
.data-analysis-page {
  display: flex;
  height: 100vh;
  background: var(--apple-bg-gradient);
}

/* 文本选择高亮动画 */
@keyframes highlightPulse {
  0% {
    background: rgba(102, 126, 234, 0.5);
    transform: scale(1.02);
  }
  50% {
    background: rgba(102, 126, 234, 0.3);
  }
  100% {
    background: rgba(102, 126, 234, 0.2);
    transform: scale(1);
  }
}

/* 可选择文本区域的样式 */
.report-content-selectable {
  cursor: text;
}

.report-content-selectable ::selection {
  background: rgba(102, 126, 234, 0.3);
}

.report-content-selectable :deep(.text-selection-highlight) {
  background: linear-gradient(120deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.3) 100%);
  border-radius: 4px;
  padding: 2px 0;
  animation: highlightPulse 0.5s ease-out;
}

/* 历史会话栏容器 */
.sidebar-container {
  position: relative;
  height: 100vh;
  flex-shrink: 0;
  display: flex;
}

.sidebar-container :deep(.history-sidebar) {
  width: 100%;
  flex: 1;
}

/* 历史会话栏拖拽分隔条 */
.sidebar-resize-handle {
  width: 4px;
  height: 100%;
  background: transparent;
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  position: absolute;
  right: 0;
  top: 0;
  z-index: 10;
  transition: background-color 0.2s;
}

.sidebar-resize-handle:hover {
  background: rgba(255, 255, 255, 0.1);
}

.sidebar-resize-handle .resize-handle-line {
  width: 2px;
  height: 40px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 1px;
}

.sidebar-resize-handle:hover .resize-handle-line {
  background: rgba(255, 255, 255, 0.6);
}

.main-content {
  flex: 1;
  padding: var(--apple-space-2xl);
  overflow-y: auto;
  background: var(--apple-bg-primary);
  position: relative; /* 为对话模式提供定位上下文 */
}

/* 对话模式时，隐藏padding，让对话布局占满整个区域 */
.main-content:has(.dialog-mode-layout) {
  padding: 0;
  overflow: hidden;
}

.data-analysis-page:has(.dify-embed-container) .main-content {
  width: 100%;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--apple-space-2xl);
  padding-bottom: var(--apple-space-2xl);
  border-bottom: 1px solid var(--apple-border-light);
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.workflow-status-bar {
  margin-bottom: 16px;
}

.mode-switch {
  margin-bottom: 20px;
  display: flex;
  justify-content: flex-end;
}

/* AI对话模式布局 - 占满整个主内容区 */
.dialog-mode-layout {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  gap: 0;
  background: #ffffff;
  overflow: hidden;
  z-index: 10;
}

/* 当有历史会话栏时，对话模式需要考虑左侧栏的宽度 */
.data-analysis-page:has(.history-sidebar) .dialog-mode-layout {
  left: 0; /* 相对于main-content，不需要额外偏移 */
}

.dialog-left-panel {
  height: 100%;
  background: #f8f9fa;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

/* 拖拽分隔条 */
.resize-handle {
  width: 8px;
  height: 100%;
  background: #f0f0f0;
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  flex-shrink: 0;
  transition: background-color 0.2s;
}

.resize-handle:hover {
  background: #e0e0e0;
}

.resize-handle:active {
  background: #d0d0d0;
}

.resize-handle-line {
  width: 2px;
  height: 40px;
  background: #999;
  border-radius: 1px;
}

.resize-handle:hover .resize-handle-line {
  background: #666;
}

.resize-tooltip {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  pointer-events: none;
  z-index: 1000;
}

.dialog-right-panel {
  height: 100%;
  overflow-y: auto;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.report-display {
  flex: 1;
  padding: 40px;
  overflow-y: auto;
}

.report-text {
  margin-bottom: 32px;
  line-height: 1.8;
  color: #333;
  font-size: 15px;
}

.report-text :deep(h1),
.report-text :deep(h2),
.report-text :deep(h3) {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  color: #1d1d1f;
}

.report-text :deep(p) {
  margin-bottom: 16px;
}

.chart-action-section {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}

.html-charts-preview {
  margin-top: 24px;
  position: relative;
  
  &.clickable-chart {
    cursor: pointer;
    transition: all 0.3s ease;
    border-radius: 8px;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
      
      .html-charts-iframe {
        border-color: #409eff;
      }
      
      .chart-click-overlay {
        opacity: 1;
      }
    }
  }
  
  .chart-click-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(64, 158, 255, 0.05);
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.3s ease;
    z-index: 10;
    border-radius: 8px;
    
    .click-hint {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 24px;
      background: rgba(64, 158, 255, 0.9);
      color: #fff;
      border-radius: 24px;
      font-size: 14px;
      font-weight: 500;
      box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
      
      .el-icon {
        font-size: 18px;
      }
    }
  }
}

.html-charts-iframe {
  width: 100%;
  min-height: 700px;
  border: none;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.report-charts {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.chart-container {
  background: #ffffff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.chart {
  width: 100%;
  height: 400px;
}

.dify-embed-container {
  width: 100%;
  height: calc(100vh - 300px);
  min-height: 700px;
  border: 1px solid var(--apple-border-light);
  border-radius: var(--apple-radius-lg);
  overflow: hidden;
  background: var(--apple-bg-primary);
  box-shadow: var(--apple-shadow-md);
}

.header-text {
  border-bottom: none;
}

.header-text h1 {
  margin: 0 0 var(--apple-space-sm) 0;
  font-size: var(--apple-font-2xl);
  font-weight: 600;
  color: var(--apple-text-primary);
  letter-spacing: -0.3px;
}

.header-text p {
  margin: 0;
  color: var(--apple-text-secondary);
  font-size: var(--apple-font-sm);
}

.upload-section {
  margin-bottom: 24px;
}

.excel-uploader {
  width: 100%;
}

:deep(.el-upload-dragger) {
  width: 100%;
  padding: var(--apple-space-4xl);
  border: 2px dashed var(--apple-border);
  border-radius: var(--apple-radius-lg);
  background: var(--apple-bg-primary);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

:deep(.el-upload-dragger:hover) {
  border-color: var(--apple-primary);
  background: rgba(0, 122, 255, 0.02);
  box-shadow: var(--apple-shadow-sm);
}

.upload-icon {
  font-size: 48px;
  color: var(--apple-primary);
  margin-bottom: var(--apple-space-lg);
}

.upload-text {
  text-align: center;
}

.upload-text p {
  margin: var(--apple-space-sm) 0;
  color: var(--apple-text-primary);
  font-size: var(--apple-font-base);
}

.upload-hint {
  color: var(--apple-text-secondary);
  font-size: var(--apple-font-sm);
}

.upload-tip {
  margin-top: 16px;
  text-align: center;
}

.upload-progress {
  margin-top: 16px;
}

.input-section {
  margin-bottom: var(--apple-space-2xl);
  padding: var(--apple-space-2xl);
  background: var(--apple-bg-primary);
  border-radius: var(--apple-radius-lg);
  border: 1px solid var(--apple-border-light);
  box-shadow: var(--apple-shadow-sm);
}

.input-header {
  margin-bottom: var(--apple-space-lg);
}

.input-header h3 {
  margin: 0;
  font-size: var(--apple-font-xl);
  font-weight: 600;
  color: var(--apple-text-primary);
  letter-spacing: -0.2px;
}

.input-examples {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.example-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.example-tag:hover {
  background: var(--notion-primary);
  color: #fff;
}

.submit-section {
  margin-top: 24px;
  text-align: center;
}

.report-section {
  margin-top: var(--apple-space-2xl);
  padding: var(--apple-space-2xl);
  background: var(--apple-bg-primary);
  border-radius: var(--apple-radius-lg);
  border: 1px solid var(--apple-border-light);
  box-shadow: var(--apple-shadow-md);
}

.report-message {
  display: flex;
  gap: 16px;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--apple-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 20px;
  flex-shrink: 0;
  box-shadow: var(--apple-shadow-sm);
}

.message-content {
  flex: 1;
}

.report-text {
  color: var(--apple-text-primary);
  line-height: 1.8;
  margin-bottom: var(--apple-space-xl);
  
  :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
    margin-top: 16px;
    margin-bottom: 8px;
    font-weight: 600;
    line-height: 1.3;
  }
  
  :deep(h1) { font-size: 1.8em; }
  :deep(h2) { font-size: 1.5em; }
  :deep(h3) { font-size: 1.3em; }
  
  :deep(p) {
    margin: 8px 0;
    word-break: break-word;
  }
  
  :deep(code) {
    background: rgba(0, 0, 0, 0.05);
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
  }
  
  :deep(pre) {
    background: rgba(0, 0, 0, 0.05);
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
    margin: 12px 0;
    
    code {
      background: none;
      padding: 0;
    }
  }
  
  :deep(ul), :deep(ol) {
    margin: 8px 0;
    padding-left: 24px;
  }
  
  :deep(li) {
    margin: 4px 0;
  }
  
  :deep(blockquote) {
    border-left: 3px solid var(--el-color-primary);
    padding-left: 12px;
    margin: 12px 0;
    color: var(--notion-text-secondary);
  }
  
  :deep(table) {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    
    th, td {
      border: 1px solid var(--notion-border);
      padding: 8px;
      text-align: left;
    }
    
    th {
      background: rgba(0, 0, 0, 0.05);
      font-weight: 600;
    }
  }
  
  :deep(a) {
    color: var(--el-color-primary);
    text-decoration: none;
    
    &:hover {
      text-decoration: underline;
    }
  }
  
  :deep(strong) {
    font-weight: 600;
  }
  
  :deep(em) {
    font-style: italic;
  }
}

/* 图表操作按钮区域 */
.chart-action-section {
  margin-top: 20px;
  margin-bottom: 20px;
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

/* 可选：图表预览区域 */
.html-charts-preview {
  margin-top: 20px;
  margin-bottom: 20px;
  border: 1px solid var(--notion-border);
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--apple-bg-secondary, #f5f5f5);
  border-bottom: 1px solid var(--notion-border);
  
  span {
    font-size: 14px;
    font-weight: 500;
    color: var(--apple-text-primary, #333);
  }
}

.html-charts-iframe-preview {
  width: 100%;
  min-height: 400px;
  height: auto;
  border: none;
  display: block;
  background: white;
}

/* HTML图表容器样式（保留用于向后兼容） */
.html-charts-container {
  margin-top: 20px;
  margin-bottom: 20px;
  border: 1px solid var(--notion-border);
  border-radius: 8px;
  overflow: auto; /* 允许滚动，防止内容溢出 */
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  max-width: 100%; /* 确保不超出父容器 */
}

.html-charts-iframe {
  width: 100%;
  min-height: 600px; /* 合理的最小高度 */
  max-height: 1000px; /* 限制最大高度，避免过长 */
  height: auto;
  border: none;
  display: block;
  background: white;
  transition: height 0.3s ease;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .html-charts-iframe {
    min-height: 400px;
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .html-charts-iframe {
    min-height: 600px;
  }
}

.report-charts {
  margin: 20px 0;
}

.chart-container {
  margin-bottom: 24px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid var(--notion-border);
}

.chart {
  width: 100%;
  height: 400px;
}

.report-tables {
  margin: 20px 0;
}

.report-actions {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--notion-border);
}

.flow-info {
  margin-top: 24px;
}

.flow-info-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 历史报告显示模式样式 */
.history-report-container {
  padding: 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 12px 16px;
  background: var(--apple-bg-secondary, #f5f5f5);
  border-radius: 8px;
  
  .chart-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--apple-text-primary, #333);
  }
}

.chart-preview {
  margin-top: 12px;
}

/* AI对话面板样式 */
.main-content {
  transition: all 0.3s ease;

  &.with-dialog {
    display: flex;
    gap: 20px;

    .content-body {
      flex: 2;
    }
  }
}

/* 对话面板容器 */
.dialog-panel-container {
  flex: 1;
  min-width: 350px;
  max-width: 450px;
}

/* 版本提示条 */
.version-banner {
  margin-bottom: 16px;
}

.version-banner-content {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.version-banner-content .version-summary {
  color: #606266;
  font-weight: normal;
}

.version-banner-content .version-time {
  color: #909399;
  font-size: 13px;
}

.version-banner :deep(.el-alert__content) {
  display: flex;
  align-items: center;
  width: 100%;
}

.version-banner :deep(.el-alert__title) {
  flex: 1;
  margin-bottom: 0;
}
</style>


