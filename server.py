import asyncio
import os
import aiofiles

async def handle_client(reader, writer):
    try:
        addr = writer.get_extra_info('peername')
        while True:
            print(f"waiting for request from {addr}")
            request = await reader.read(1)
            request = request.decode()
            print(f"command {request} from {addr}")
            if request == "0":
                print(f'Closing connection of {addr}')
                writer.close()
                await writer.wait_closed()
                print(f"✻ Client {addr} disconnected.")
                break
            if request == "1":
                await send_file(reader, writer)
            if request == "2":
                await download_file(reader, writer)
    except ConnectionResetError:
        print(f"✻ {addr} The specified network is no longer available.")

async def send_file(reader, writer):
    filename = (await reader.read(1024)).decode()
    
    if os.path.isfile(filename):
        writer.write(b'file_available')
        await writer.drain()

        async with aiofiles.open(filename, 'rb') as f:
            while True:
                data = await f.read(4096)
                if not data:
                    await send_chunk(b'eof', writer)
                    break
                await send_chunk(data, writer)
        print("File was sent sucessfully.")
    else:
        writer.write(b'file_not_available')
        await writer.drain()
        print("Requested file is not on server.")

async def download_file(reader, writer):
    filename = (await reader.read(1024)).decode()
    if not os.path.isfile(f"uploaded_{filename}"):
        writer.write(b'no_duplicate_file')
        await writer.drain()
        async with aiofiles.open(f"uploaded_{filename}", 'wb') as f:
            while True:
                data = await recv_chunk(reader)
                if data == b'eof':
                    break
                await f.write(data)
        print("Sucessfully downloaded file.")
    else:
        writer.write(b'duplicate_file')
        await writer.drain()
        print("File with same name is on server.")

async def recv_chunk(reader):
    prefix = await reader.readline()
    chunk_len = int(prefix)
    return await reader.readexactly(chunk_len)
         
async def send_chunk(content, writer):
    writer.write(b'%d\n' % len(content))
    writer.write(content)
    await writer.drain()           

async def main():
    server = await asyncio.start_server(handle_client, '127.0.0.1', 8888)

    async with server:
        await server.serve_forever()
    

asyncio.run(main())
