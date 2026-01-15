uv run uvicorn app.main:app --reload

Hãy thêm file .env vào 
~
uvicorn app.main:app --host 0.0.0.0 --port 8000


DATABASE_URL = "Db string"
SECRET_KEY = "Cái này thì ghi gì cũng được"
ASYNC_DATABASE_URL = "postgresql+asyncpg://......."
N8N_WEBHOOK_URL = "....."
HLS_DIR=D:/Hls
~
HLS_DIR = Chỗ để lưu m3u8 + ts file tạm cho live view 

Thay url domain để Fetch API tại file config.js

nếu thêm model mới thì import vào env.py của alembic thì mới autogenerate đc 


Styles dùng tailwind online == cần có mạng
tìm cách tải về cũng đc . It possible ( and not that hard maybe )

be độc lập  
"D:\PostGreSql\bin\pg_dump.exe" -U postgres -h localhost -p 5432 -d ForBackEnd -F c -b -v -f D:\BackUpDb\backup.dump


Cái live view bắt rtsp và decode == ffmpeg, ffmpeg-python lib chỉ là ffmpeg wapper giúp sinh script thôi, muốn chạy vẫn cần cài ffmpeg vào Path của máy 

uv run uvicorn app.main:app --host 0.0.0.0 --port 8000  --reload


uv run uvicorn app.main:app --host 128.1.7.201 --port 8000  --reload