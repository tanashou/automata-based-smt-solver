# 卒論

オートマトンを用いたプレスブルガー算術式の充足可能性判定法

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [参考文献](#参考文献)
- [License](#license)

## Installation
If you want a visualized graph, you need `pygraphviz`. For mac, install graphviz via homebrew
```bash
brew install graphviz
```
add these lines to .zshrc
```bash
export CFLAGS="-I $(brew --prefix graphviz)/include"
export LDFLAGS="-L $(brew --prefix graphviz)/lib"
```

then run `rye sync`.

If you don't need a visualized graph, you need to run this command
```bash
rye remove automata-lib
rye sync
```
## Usage

TODO

## 参考文献

## License

TODO
