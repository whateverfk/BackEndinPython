uv run uvicorn app.main:app --reload

Hãy thêm file .env vào 
~

DATABASE_URL = "Db string"
SECRET_KEY = "Cái này thì ghi gì cũng được"
ASYNC_DATABASE_URL = "postgresql+asyncpg://......."
~
Thay url domain để Fetch API tại file config.js

nếu thêm model mới thì import vào env.py của alembic thì mới autogenerate đc 


Styles dùng tailwind online == cần có mạng
tìm cách tải về cũng đc . It possible ( and not that hard maybe )

be độc lập  
"D:\PostGreSql\bin\pg_dump.exe" -U postgres -h localhost -p 5432 -d ForBackEnd -F c -b -v -f D:\BackUpDb\backup.dump


Cái live view bắt rtsp và decode == ffmpeg, ffmpeg-python lib chỉ là ffmpeg wapper giúp sinh script thôi, muốn chạy vẫn cần cài ffmpeg vào Path của máy 