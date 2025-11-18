from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

print("Đang tải model về thư mục ./models ...")

tokenizer = AutoTokenizer.from_pretrained(
    "google/flan-t5-small",
    cache_dir="./models"
)

model = AutoModelForSeq2SeqLM.from_pretrained(
    "google/flan-t5-small",
    cache_dir="./models"
)

print("✅ Tải xong, lần sau không cần tải lại.")

