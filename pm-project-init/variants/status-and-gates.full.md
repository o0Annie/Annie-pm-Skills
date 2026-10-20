# 需求状态和阶段门槛

## 需求状态流转

```text
candidate → collecting → analyzing → defined → reviewing → approved → developing → validating → released → closed
```

## 关键规则

- 状态只在需求池维护，不在其他地方复制
- approved 后发生实质变化时，记录变更并回到 reviewing
- released 必须有真实上线验证证据
