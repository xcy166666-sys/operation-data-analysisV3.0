# 安装测试依赖

## 步骤

请在frontend目录下运行以下命令安装测试依赖：

```bash
cd frontend
npm install --save-dev vitest@^1.0.0 @vitest/ui@^1.0.0 fast-check@^3.15.0 @vue/test-utils@^2.4.0 happy-dom@^12.10.0
```

## 验证安装

安装完成后，运行以下命令验证：

```bash
npm test
```

应该看到测试运行并通过。

## 如果遇到问题

### 问题1：npm install失败
尝试清除缓存：
```bash
npm cache clean --force
npm install
```

### 问题2：版本冲突
检查package.json中的版本是否与现有依赖兼容。

### 问题3：测试无法运行
确保vitest.config.ts文件存在且配置正确。

## 下一步

安装完成后，可以：
1. 运行 `npm test` 查看测试基础设施是否正常
2. 运行 `npm run test:ui` 打开可视化测试界面
3. 开始实施任务2：实现HTML图表解析器
