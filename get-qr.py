import qrcode
from socket import gethostname, gethostbyname
from subprocess import run
from flask import cli as flask_cli, Flask, send_file, Response, redirect, request, render_template_string
from threading import Thread
from pathlib import Path
from os import PathLike
from typing import Union
from random import choices
from string import ascii_letters, digits
from logging import getLogger
from datetime import datetime
from sys import argv, exit

app = Flask(__name__)

flask_cli.show_server_banner = lambda *args: None
getLogger('werkzeug').disabled = True

generated_id = None

def show_qrcode_in_terminal(link: str) -> None:
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=2, border=1)
    qr.add_data(link)
    qr.make(fit=True)
    matrix = qr.get_matrix()

    print(' ' * (len(matrix) * 2 + 4))
    for row in matrix:
        print('  ', end='')
        for cell in row:
            print('██' if not cell else '  ', end='')
        print('  ')
    print(' ' * (len(matrix) * 2 + 4))

def set_random_id() -> None:
    global generated_id
    generated_id = ''.join(choices(ascii_letters + digits, k=8))

def generate_file_download_url(file_path: Union[PathLike, Path, str], port: int) -> dict:
    hostname = gethostbyname(gethostname())
    return {
        'local_url': f'http://{hostname}:{port}/i/{file_path}',
        'online_url': f'http://{hostname}:{port}/r/{generated_id}'
    }

def serve_http_server(port: int) -> None:
    app.run(host='0.0.0.0', port=port, threaded=True, debug=False)

def main(file_path: Union[PathLike, Path, str]) -> None:
    global generated_id

    @app.route('/i/<path:filename>')
    def serve_file(filename: str) -> Union[tuple[dict, int], Response]:
        uuid = request.args.get('uuid')
        if not uuid or generated_id != uuid.strip():
            return {'error': 'You do not have access to this file'}, 403

        file = Path(filename)
        if not file.is_file():
            return {'error': 'File not found'}, 404

        return send_file(file.resolve(), as_attachment=True)

    @app.route('/r/<uuid>')
    def redirect_url(uuid: str) -> Union[tuple[dict, int], Response]:
        if not uuid or generated_id != uuid.strip():
            return {'error': 'Invalid UUID'}, 404
        return redirect(f'{server_file_local_url}?uuid={uuid}', code=302)

    set_random_id()
    file_path = Path(file_path).resolve()
    if not file_path.is_file():
        print(f'The file path is invalid or the file does not exist! Input: "{file_path}"')
        exit(1)

    run('cls || clear', shell=True)

    server_port = 8080
    server_thread = Thread(target=serve_http_server, args=(server_port,))
    server_thread.daemon = True
    server_thread.start()

    urls = generate_file_download_url(file_path, server_port)
    global server_file_local_url
    server_file_local_url, server_file_online_url = urls['local_url'], urls['online_url']
    show_qrcode_in_terminal(server_file_online_url)

    input(f'\nFile successfully hosted! - URL: {server_file_online_url} - Press Enter to stop the server...')
    exit(0)

if __name__ == '__main__':
    if len(argv) >= 2:
        main(' '.join(argv[1:]))
    else:
        run('cls || clear', shell=True)
        folder_name = datetime.now().strftime("%Y%m%d")
        Path(folder_name).mkdir(parents=True, exist_ok=True)

        server_port = 8080
        server_thread = Thread(target=serve_http_server, args=(server_port,))
        server_thread.daemon = True
        server_thread.start()

        show_qrcode_in_terminal(f'http://{gethostbyname(gethostname())}:{server_port}/up')

        @app.route('/up', methods=['GET', 'POST'])
        def upload_file() -> Union[tuple[str, int], str, Response]:
            if request.method == 'POST':
                file = request.files['file']
                if file:
                    file.save(Path(folder_name, file.filename))
                    return 'File uploaded successfully', 200
            return render_template_string('''
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Upload File</title>
                    <style>
                        body { font-family: Arial, sans-serif; background-color: #222; color: #fff; margin: 0; padding: 0; }
                        .container { max-width: 500px; margin: 50px auto; padding: 20px; background-color: #333; border-radius: 5px; box-shadow: 0 0 10px rgba(255, 255, 255, 0.1); }
                        h2 { text-align: center; margin-bottom: 20px; }
                        form { text-align: center; }
                        input[type="file"] { display: none; }
                        .custom-file-upload { border: 1px solid #ccc; display: inline-block; padding: 10px 20px; cursor: pointer; background-color: #555; border-radius: 5px; margin-bottom: 20px; color: #fff; }
                        .custom-file-upload:hover { background-color: #777; }
                        button[type="submit"] { margin-top: 10px; padding: 10px 20px; background-color: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; }
                        .progress-bar { width: 100%; background-color: #444; border-radius: 5px; margin-top: 20px; overflow: hidden; }
                        .progress { width: 0%; height: 20px; background-color: #4CAF50; border-radius: 5px; transition: width 0.3s ease; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2>Upload File</h2>
                        <form method="POST" enctype="multipart/form-data">
                            <label for="file-upload" class="custom-file-upload">Select file</label>
                            <input id="file-upload" type="file" name="file" onchange="submitForm()">
                            <button type="submit" style="display: none;">Upload</button>
                        </form>
                        <div class="progress-bar">
                            <div class="progress" id="progress-bar"></div>
                        </div>
                    </div>
                    <script>
                        function submitForm() {
                            document.querySelector('button[type="submit"]').click();
                        }
                        document.querySelector('input[type="file"]').addEventListener('change', function () {
                            var progressBar = document.getElementById('progress-bar');
                            var fileInput = document.querySelector('input[type="file"]');
                            var file = fileInput.files[0];
                            var xhr = new XMLHttpRequest();
                            xhr.upload.onprogress = function (event) {
                                if (event.lengthComputable) {
                                    var percentComplete = (event.loaded / event.total) * 100;
                                    progressBar.style.width = percentComplete + '%';
                                }
                            };
                            xhr.open('POST', '/up', true);
                            var formData = new FormData();
                            formData.append('file', file);
                            xhr.send(formData);
                        });
                    </script>
                </body>
                </html>
            ''')

        input(f'\nFile upload server successfully hosted! - URL: http://{gethostbyname(gethostname())}:{server_port}/up - Press Enter to stop the server...')
        exit(0)
