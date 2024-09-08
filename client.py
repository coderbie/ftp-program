import asyncio
import aiofiles
import os

async def request_file(reader, writer):
    filename = input("Requesting filename: ")
    writer.write(filename.encode())
    await writer.drain()

    is_file = await reader.read(255)

    if is_file == b'file_available':
        async with aiofiles.open(f"recieved_{filename}", 'wb') as f:
            while True:
                data = await recv_chunk(reader)
                if data == b'eof':
                    break
                await f.write(data)
        print("Sucessfully recieved file.")
    else:
        print("File is not on server.")

async def upload_file(filename, reader, writer):
    writer.write(filename.encode())
    await writer.drain()
    is_duplicate = await reader.read(255)
    if is_duplicate == b'no_duplicate_file':
        async with aiofiles.open(filename, 'rb') as f:
            while True:
                data = await f.read(4096)
                if not data:
                    await send_chunk(b'eof', writer)
                    break
                await send_chunk(data, writer)
        print("File was uploaded on server sucessufully.")
    else:
        print("File with same name is already on server.")

async def recv_chunk(reader):
    prefix = await reader.readline()
    chunk_len = int(prefix)
    return await reader.readexactly(chunk_len)

async def send_chunk(content, writer):
    writer.write(b'%d\n' % len(content))
    writer.write(content)
    await writer.drain()

async def main():
    try:
        reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
        while True:
            command = input("command: ")
            if command == "0":
                writer.write('0'.encode())
                await writer.drain()
                writer.close()
                await writer.wait_closed()
                print("Disconnected from server.")
                break
            if command == "1":
                writer.write('1'.encode())
                await writer.drain()
                await request_file(reader, writer)
            if command == "2":
                filename = input("Uploading filename: ")
                if os.path.isfile(filename):
                    writer.write('2'.encode())
                    await writer.drain()
                    await upload_file(filename, reader, writer)
    except ConnectionResetError:
        print("✻ Connection lost from the server or server is closed.")
    except ConnectionRefusedError:
        print("✻ Connection denied or server is not available.")
asyncio.run(main())
