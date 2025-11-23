<div align="center">
  <img src="https://raw.githubusercontent.com/PStarH/VisiLens/main/assets/banner.svg" alt="VisiLens Logo" width="100%" />
  
  # VisiLens

  **開発者専用Excel**

  > **100万行を数秒で開く - ローカル動作、高速、軽量。**
  
  データセット探索のための高性能かつローカルファーストなWeb GUIです。[VisiData](https://www.visidata.org/) のパワーを活用して、CSV、Parquet、Excel、JSONファイルを瞬時に表示・フィルタリングできます。

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
  [![VisiData Engine](https://img.shields.io/badge/Engine-VisiData-orange.svg)](https://www.visidata.org/)
  [![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
  [![React](https://img.shields.io/badge/Frontend-React-61DAFB.svg)](https://reactjs.org/)
  [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
  [![PyPI](https://img.shields.io/pypi/v/vdweb.svg)](https://pypi.org/project/vdweb/0.1.1/)

  [English](../README.md) • [简体中文](README_zh.md) • [Español](README_es.md) • [日本語](README_ja.md) • [Русский](README_ru.md)

  [機能](#機能) • [インストール](#インストール) • [使い方](#使い方) • [アーキテクチャ](#アーキテクチャ) • [貢献](#貢献)
</div>

---

## 🚀 VisiLensを選ぶ理由

データ探索のたびに、退屈なPandasコードを書いたり、Excelのような重いスプレッドシートソフトの起動を待つ必要はもうありません。**VisiLens**は、**VisiData**の圧倒的な高速処理と軽量Webインターフェースを融合させた、モダンな**CSVビューア**兼**Parquetエクスプローラ**です。

- **⚡️ 100万行を2秒未満でロード:** 高度に最適化されたVisiDataエンジンを搭載。
- **🔒 完全ローカル動作:** データが端末の外に出ることはなく、クラウドにアップロードされることもありません。
- **🛠 ゼロコンフィグ:** CLIファーストのワークフローで、データをパイプで渡し、探索し、すぐにコーディングへ戻れます。
- **🔌 広範なフォーマット対応:** CSV、TSV、JSON、Parquet、Excel、SQLite など [50以上の形式](https://www.visidata.org/formats/) をサポート。

## ✨ 機能

- **瞬時のデータ可視化:** `vdweb data.csv` を実行するだけで、大規模なデータセットを即座に可視化できます。
- **バックエンド駆動型のソートとフィルタリング:** VisiDataエンジンを用いて、数百万行規模の複雑なクエリも軽快に処理します。
- **軽量なデータテーブル:** 仮想化されたReactベースのテーブルビューにより、大量行でもスムーズにスクロールできます。
- **ゼロコンフィグ:** データベースのセットアップは不要で、スタンドアロンのCSV/Parquetビューアとしてすぐに使えます。

### 📂 サポートされている形式
VisiLens は VisiData のローダーを活用して、さまざまな形式をすぐにサポートします。
- **表形式:** `.csv`, `.tsv`, `.xlsx` (Excel), `.parquet`
- **構造化:** `.json`, `.jsonl`, `.yaml`
- **データベース:** `.sqlite`, `.db`
- **コード:** `.pcap` (Wireshark), `.xml`, `.html` テーブル

## 📊 ベンチマーク

パフォーマンスは徹底的に追求しています。標準的なMacBook Air (M2)で**1,000,000行**のCSVデータセットを開いたときの比較は次のとおりです。

| ツール | ロード時間 (100万行) | メモリフットプリント | インタラクティブなソート |
| :--- | :--- | :--- | :--- |
| **VisiLens** | **~1.7秒** | **最小 (< 50MB 合計)** | **瞬時** (バックエンド: < 0.4秒) |
| Excel | > 30秒 (頻繁に失敗) | 高 (RAM をブロック) | 遅い/応答なし |
| **Pandas ベースの GUI** | > 15秒 (コールドスタート) | 高 (DF 全体を RAM に) | 動作が重い (非仮想化) |
| Jupyter (print df) | 速い | 中 | 静的テキスト |

*テストデータ仕様: 100万行・3列（混合型）。計測値は、実際の開発用途で使用しているMacBook Air M2上での実測に基づきます。*

## 📦 インストール

VisiLens は Python パッケージとして入手可能です。

```bash
pip install vdweb
```

*注意: VisiLens には Python 3.10 以降が必要です。*

## 💻 使い方

### コマンドラインインターフェース

VisiLens を使用する主な方法は、コマンドラインを使用することです。

```bash
# CSV ファイルを開く
vdweb data.csv

# Parquet ファイルを開く
vdweb large-dataset.parquet

# Excel ファイルを開く
vdweb spreadsheet.xlsx

# ブラウザを自動的に開かずに起動する
vdweb data.json --no-browser

# カスタムポートを指定する
vdweb data.csv --port 9000
```

### Web インターフェース

起動すると、VisiLens はデフォルトのブラウザ（通常は `http://localhost:8000`）で開きます。

1.  **データの表示:** データセットを効率的にスクロールします。
2.  **ソート:** 列ヘッダーをクリックして、昇順/降順でソートします。
3.  **フィルタ:** フィルタ入力を使用して、列内を検索します。
4.  **新しいデータのロード:** (近日公開) ファイルをウィンドウに直接ドラッグアンドドロップします。

## 🏗 アーキテクチャ

VisiLens は、パフォーマンスのために設計された堅牢で最新のスタック上に構築されています。

*   **バックエンド:** FastAPI サーバーが VisiData とブラウザを橋渡しします。
*   **通信:** WebSocket がオンデマンドでスライスをストリーミングします。
*   **フロントエンド:** React グリッドは、表示されているものだけをレンダリングします。

![アーキテクチャ図](https://raw.githubusercontent.com/PStarH/VisiLens/main/assets/diagram.png)

## 🗺 ロードマップ

私たちは、VisiLens を究極のローカルデータコンパニオンにするために積極的に取り組んでいます。

- [x] **v0.1:** コアエンジン、仮想スクロール、ソート、フィルタリング。
- [ ] **Jupyter 統合:** ノートブックセルから直接 VisiLens を起動します (`visilens.view(df)`)。
- [ ] **ドラッグアンドドロップによるファイルロード**
- [ ] **プロット:** Vega-Lite によるクイックヒストグラムと散布図。
- [ ] **編集:** セルを編集し、変更を CSV/Parquet に保存します。
- [ ] **SQL サポート:** SQLite/Postgres/DuckDB に直接接続します。

## 🛠 開発

貢献に興味がありますか？大歓迎です！開発環境のセットアップ方法は次のとおりです。

### 前提条件

- Python 3.10+
- Node.js 18+
- npm または pnpm

### セットアップ

1.  **リポジトリのクローン**
    ```bash
    git clone https://github.com/PStarH/VisiLens.git
    cd VisiLens
    ```

2.  **バックエンドのセットアップ**
    ```bash
    # 仮想環境の作成
    python -m venv .venv
    source .venv/bin/activate  # Windows の場合は .venv\Scripts\activate

    # 依存関係のインストール
    pip install -e ".[dev]"
    ```

3.  **フロントエンドのセットアップ**
    ```bash
    cd frontend
    npm install
    ```

4.  **ローカルでの実行**

  ターミナル 1 (バックエンド):
  ```bash
  uvicorn backend.main:app --reload --port 8000
  ```

  ターミナル 2 (フロントエンド):
  ```bash
  cd frontend
  npm run dev
  ```

5.  **フロントエンドアセットのビルド (オプション)**

  Python CLI のみを実行したい場合（別の Vite 開発サーバーなし）、フロントエンドを一度ビルドできます。

  ```bash
  cd frontend
  npm run build
  ```

  これにより、`frontend/dist/` 下に本番バンドルが生成され、リリースのために `vdweb/static/` にコピーされます。エンドユーザーは以下を実行するだけです。

  ```bash
  vdweb path/to/data.csv
  ```

## 🤝 貢献

### 貢献者のために：何がどこにあるか

- **Python パッケージ (`vdweb/`):** これは PyPI に公開されるインストール可能なパッケージです。CLI エントリポイント `vdweb` / `visilens` は、`pyproject.toml` で構成されているように、どちらも `vdweb.cli:main` に解決されます。
- **開発バックエンド (`backend/`):** ローカル開発のみに使用される別の FastAPI アプリ (`uvicorn backend.main:app`) です。パッケージ化されたバックエンドの動作をミラーリングしますが、ユーザーが `vdweb` をインストールするときにインポートするものではありません。
- **コアロジック:** VisiData 駆動のデータアクセスレイヤーは `vdweb/core.py` にあります（開発アプリのために `backend/core.py` にミラーリングされています）。データのロード/ソート/フィルタリング方法を変更したい場合は、ここから始めてください。

### 一般的な貢献者のワークフロー

1. `vdweb/` 内のバックエンド/コアロジックを編集します（開発のパリティが必要な場合は `backend/` も更新します）。
2. [開発](#-開発) で説明されているように、開発バックエンド + フロントエンドをローカルで実行します。
3. React アプリを変更し、それらの変更を出荷したい場合は、`frontend/` で `npm run build` を実行して、`vdweb/static/` にコピーされるバンドルが最新になるようにします。

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。詳細については [LICENSE](../LICENSE) ファイルを参照してください。

---

<div align="center">
  <a href="https://github.com/PStarH">PStarH</a> とオープンソースコミュニティによって ❤️ で作られました。
</div>

---
*この README は AI によって翻訳されており、レビューされていません。改善のための PR をお気軽に送信してください。*
