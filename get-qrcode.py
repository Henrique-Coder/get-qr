import qrcode
from socket import gethostname, gethostbyname
from subprocess import run
from flask import Flask, send_file, Response, redirect, request
from threading import Thread
from pathlib import Path
from os import PathLike
from typing import Union
from argparse import ArgumentParser
from platform import system
from random import choice
from string import ascii_letters, digits
from sys import exit


generated_id = None

app = Flask(__name__)


def change_terminal_size(width: int, height: int) -> None:
    try:
        if system() == 'Windows':
            run(f'mode con: cols={width} lines={height} >nul 2>&1', shell=True)
        elif system() == 'Linux' or system() == 'Darwin':
            run(f'stty cols {width} rows {height}', shell=True)
        else:
            pass
    except BaseException:
        pass


def show_qrcode_in_terminal(link: str) -> None:
    qr = qrcode.main.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=2, border=1)
    qr.add_data(link)
    qr.make(fit=True)
    matrix = qr.get_matrix()

    print(' ' * (len(matrix) * 2 + 4))

    for i in range(len(matrix)):
        print('  ', end=str())
        for j in range(len(matrix)):
            if matrix[i][j]:
                print('  ', end=str())
            else:
                print('██', end=str())
        print('  ')

    print(' ' * (len(matrix) * 2 + 4))


def set_random_id() -> None:
    global generated_id

    characters = ascii_letters + digits
    generated_id = str().join(choice(characters) for _ in range(8))


def generate_file_download_url(file_path: Union[PathLike, Path, str], port: int) -> dict:
    return {
        'local_url': f'http://{gethostbyname(gethostname())}:{port}/i/{file_path}',
        'online_url': f'http://{gethostbyname(gethostname())}:{port}/r/{generated_id}'
    }


def serve_http_server(port: int) -> None:
    app.run(host='0.0.0.0', port=port, threaded=True, debug=False)


def main(file_path: Union[PathLike, Path, str]) -> None:
    global generated_id

    @app.route('/i/<path:filename>')
    def serve_file(filename: str) -> Union[tuple[dict, int], Response]:
        if 'highLightTitle.png' in filename:
            return Response(status=404)

        uuid = request.args.get('uuid')
        if not uuid or not str(uuid).strip() or generated_id != uuid.strip():
            return {'error': 'You do not have access to this file'}, 403

        if not Path(filename).is_file():
            return {'error': 'File not found'}, 404

        return send_file(Path(filename).resolve(), download_name=Path(filename).name)

    @app.route('/r/<uuid>')
    def redirect_url(uuid: str) -> Union[tuple[dict, int], Response]:
        if 'highLightTitle.png' in uuid:
            return Response(status=404)

        if not uuid or not str(uuid).strip():
            return {'error': 'UUID is missing'}, 404

        if generated_id != uuid.strip():
            return {'error': 'Invalid UUID'}, 404

        return redirect(f'{server_file_local_url}?uuid={uuid}', code=302)

    run('cls', shell=True)
    change_terminal_size(width=58, height=48)

    set_random_id()

    file_path = Path(file_path).resolve()
    server_port = 8080

    data = generate_file_download_url(file_path, server_port)
    server_file_local_url, server_file_online_url = data['local_url'], data['online_url']
    show_qrcode_in_terminal(server_file_online_url)

    print(f'\nScan the QR code with your mobile device to download the file or access the link: {server_file_online_url}\n')
    print('Press Enter to end the server...\n')

    server_thread = Thread(target=serve_http_server, args=(server_port,))
    server_thread.daemon = True
    server_thread.start()

    input()

    change_terminal_size(width=80, height=25)
    exit(0)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-i', '--input-filepath', metavar='input_filepath', type=str, help='Input filepath of the file to be shared', required=True)
    args = parser.parse_args()

    main(args.input_filepath)
