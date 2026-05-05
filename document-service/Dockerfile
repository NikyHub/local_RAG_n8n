FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# 先安装你的依赖
RUN pip install --no-cache-dir -r requirements.txt

# 强制将 NumPy 降级到兼容的 1.x 版本，并补充之前缺失的库
RUN pip install --no-cache-dir "numpy<2.0.0" albumentations imgaug opencv-python-headless

# Pre-download PaddleOCR models
RUN python -c "from paddleocr import PaddleOCR; PaddleOCR(lang='ch', use_angle_cls=True)"

COPY main.py .

EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
