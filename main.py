name: Auto Patch & Deploy

on:
  schedule:
    # 通常運転（15分おき）
    - cron: "*/15 * * * *"
    # ブースト運転（5分おき）
    - cron: "*/5 * * * *"
  workflow_dispatch: {}

permissions:
  contents: write

env:
  # リポジトリ変数から運転モードを読み込み（fast / normal）
  RUN_MODE: ${{ vars.RUN_MODE }}
  # どのブランチを使うか
  TARGET_BRANCH: main

jobs:
  patch-and-deploy:
    runs-on: ubuntu-latest
    # fastモード時: 両方トリガーで動く
    # normalモード時: 15分おきのトリガーだけ動かす（5分おきは即終了）
    steps:
      - name: Early exit on schedule/mode mismatch
        run: |
          # SCHEDULE_KIND は 5分 or 15分 を判定するための環境値をActionsが持たないので、
          # 直近のトリガー間隔を疑似判別：5分境界なら 5分、そうでなければ15分扱いにする簡易ロジック
          MIN=$(date +%M)
          if [ $((10#$MIN % 5)) -eq 0 ]; then
            TRIGGER_KIND=fast    # 5分境界
          else
            TRIGGER_KIND=normal  # それ以外
          fi
          echo "RUN_MODE=${RUN_MODE:-normal}"
          echo "TRIGGER_KIND=$TRIGGER_KIND"

          if [ "${RUN_MODE:-normal}" = "normal" ] && [ "$TRIGGER_KIND" = "fast" ]; then
            echo "Normal modeなので5分トリガーは早期終了"; exit 0
          fi

      - name: Checkout
        uses: actions/checkout@v4
        with:
          ref: ${{ env.TARGET_BRANCH }}

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Apply small safe patches (if any)
        run: |
          python - << 'PY'
          # ここで安全な軽微パッチを自動適用（例：ops/desired_changes.yaml を読む等）
          # 今はダミー：将来このロジックを強化していきます
          print("No-op patch step (placeholder)")
          PY

      - name: Commit if changed
        run: |
          git config user.name "auto-bot"
          git config user.email "auto-bot@users.noreply.github.com"
          git add -A
          if git diff --cached --quiet; then
            echo "No changes to commit"
          else
            git commit -m "chore: autopatch ($(date -u +'%Y-%m-%dT%H:%M:%SZ'))"
            git push origin ${{ env.TARGET_BRANCH }}
          fi

      - name: Trigger Render deploy (optional)
        if: ${{ secrets.RENDER_DEPLOY_HOOK_URL != '' }}
        run: |
          curl -fsS -X POST "${{ secrets.RENDER_DEPLOY_HOOK_URL }}" || true