# AI理财面板（仓库名建议：licai）

个人持仓盈亏面板：基金（天天基金净值，覆盖支付宝/理财通全部公募基金）+ 股票（新浪行情，盘中15分钟延迟）。

## 使用方法
1. watchlist.json 添加你要跟踪的基金/股票代码
2. Actions 每15分钟自动更新 data.json
3. 打开网站，在"未持仓 · 录入"处输入份额和成本——持仓只存本浏览器(localStorage)

## 部署
Settings → Pages → main/(root) → Actions 手动 Run 一次
