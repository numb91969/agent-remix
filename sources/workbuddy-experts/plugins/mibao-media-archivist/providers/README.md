# Cloud provider adapter contract

秘宝的云端适配器必须提供以下只读能力：

- `capability()`：返回授权、分页、元数据、下载/流式访问能力及限制。
- `list_assets(scope, checkpoint)`：逐页返回原始响应和标准化资产，不得丢弃 provider 字段。
- `checkpoint()`：保存 cursor/serverVersion/page/hash/hasMore/finishFlag，支持 resume。
- `get_metadata(remote_id)`：读取单资产元数据。
- `download(remote_id, output)`：仅在用户确认后下载到独立派生目录。

首批适配器：Weiyun、WeCom Disk。适配器不执行删除、移动、重命名和公开操作。
