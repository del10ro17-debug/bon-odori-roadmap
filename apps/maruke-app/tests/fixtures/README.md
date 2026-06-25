# 実プリント精度検証用画像

## 3種の置き場所（CEO / ベータ家庭）

| ケース | ディレクトリ | 例 |
|--------|-------------|-----|
| 大手塾・算数 | `real/juku/` | SAPIX, 日能研, 四谷, 早アカ の算数1ページ |
| 進研 or Z会 | `real/shinken_zkai/` | 大きな数、計算ドリル1ページ |
| 国語・選択/記述 | `real/kokugo/` | 擬声語選択、短文記述（未記入含む） |

**撮影ルール:** 片ページ・明るい・真上。見開きは避ける。

## 合成スモーク（API不要の見た目確認）

`synthetic/` — `generate_test_fixtures.py` で生成

## 実行

```bash
# フィクスチャ生成（初回）
pip install pillow
python tools/maruke_app/generate_test_fixtures.py

# APIキー（Projects からコピー済みなら不要）
cp ~/Projects/maruke-app/.env apps/maruke-app/.env

# 検証実行
python tools/maruke_app/run_accuracy_test.py
```

レポート: `apps/maruke-app/tests/reports/accuracy-*.md`
