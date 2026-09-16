# 加新 inquiry-price-<id> core 的极简流程

1. **新建 skill 目录**：`plugins/cpq/skills/inquiry-price-<id>/`
2. **写 SKILL.md**（frontmatter）：

   ```yaml
   ---
   name: inquiry-price-<id>
   description: inquiry-price wrapper 的 <描述> core · 内部实现细节 · 禁止 LLM 直接加载
   ---

   # inquiry-price-<id>

   🔒 **内核 skill · 禁止 LLM 直接 use_skill 加载** ·
   合法进入方式 = 通过父级 inquiry-price wrapper · INQUIRY_PRICE_CORE=<id>
   ```

3. **实现入口脚本**：`scripts/run.py`（按 references/core-contract.md §4 接受参数 · 产 summary.xlsx 9 列）
4. **wrapper dispatch.py 加一个 elif 分支**：

   ```python
   elif core == "<id>":
       cmd = [py, str(SKILLS_ROOT / "inquiry-price-<id>" / "scripts" / "run.py"),
              "--source-table", str(source_table), "--run-dir", str(run_dir)]
       if common_context:
           cmd += ["--common-context", common_context]
       return cmd
   ```

   并把 `<id>` 加进 `SUPPORTED_CORES` list。
5. **wrapper SKILL.md 无需修改**（除非新 core 引入用户感知的新能力）
6. **plugin.json version bump** + `bun run sync:manifest` + `bun run sync:marketplace`
7. **commit** 时 commit body 加 `User-facing:` 行说明新增 core 的能力（如果用户感知）
