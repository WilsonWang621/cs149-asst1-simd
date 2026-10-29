# 本机环境使用说明（WSL）

在 **Ubuntu-Recovered 的 Bash 终端**中使用，不要直接在 PowerShell 中执行 make。

```bash
cd /home/wangwenxuan/ACM/大二上/cs149-asst1-simd
source ./env.sh
ispc --version
```

每次打开新终端后，在仓库根目录执行一次 `source ./env.sh`。该脚本将本地 ISPC 加入当前终端的 PATH，并激活 Python 虚拟环境；没有修改全局 Bash 配置。

## 已配置的工具

- Ubuntu WSL，x86-64，CPU 支持 AVX2。
- 系统已有 GCC 13.3、GNU Make 4.3、Python 3.12.3。
- ISPC 1.28.1：`.tools/ispc-v1.28.1-linux/bin/ispc`。
- Python 虚拟环境：`.venv/`。
- 绘图依赖见 `requirements-local.txt`。原始 `prog6_kmeans/requirements.txt` 的 Matplotlib 3.6 系列较旧，本机 Python 3.12 环境使用 Matplotlib 3.9.4。

## 编译与运行

激活环境后，在各实验目录运行 `make`。例如：

```bash
cd prog3_mandelbrot_ispc
make
./mandelbrot_ispc --tasks
```

从仓库根目录编译全部实验：

```bash
for project in prog1_mandelbrot_threads prog2_vecintrin prog3_mandelbrot_ispc prog4_sqrt prog5_saxpy prog6_kmeans; do
    make -C "$project" || break
done
```

实验 1、2 的待实现函数仍保留原状，编译成功后出现正确性检查失败属于作业尚未完成。实验 3、4、5 可直接运行。

实验 6 编译后还需要课程数据。把 `data.dat` 放在 `prog6_kmeans/`，然后：

```bash
cd prog6_kmeans
./kmeans
python plot.py
```

课程数据的下载位置参见 README 的 Program 6，需使用自己的课程账号。

## 重建 Python 环境

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --index-url https://pypi.org/simple -r requirements-local.txt
```

本机配置的清华 PyPI 镜像在安装时超时，以上命令显式使用官方 PyPI，不修改系统镜像设置。

## 编译兼容修复

为适配当前编译器，补齐了原代码使用的标准库声明：实验 1、3 的 `main.cpp` 加入 `<cstring>`，实验 1 的 `mandelbrotThread.cpp` 加入 `<cstdlib>`。算法和作业 TODO 未改动。

`.tools/`、`.venv/`、构建产物和实验输出已加入 `.gitignore`。本机性能测试与 README 指定的 Myth 机器不同，报告中应注明实际测试硬件。
