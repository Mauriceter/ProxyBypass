from flask import Flask, request, jsonify, render_template_string
import os
import base64

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>DLP Upload Test Suite</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background: #f9f9f9; }
        h1 { color: #2c3e50; }
        .section { margin-bottom: 40px; background: #fff; padding: 20px; border-radius: 8px; 
                   box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
        #dropZone { cursor: pointer; }
        button { margin: 5px 5px 0 0; padding: 10px 15px; border: none; border-radius: 4px; 
                 background: #3498db; color: white; cursor: pointer; }
        button:hover { background: #2980b9; }
        input[type="file"] { width: 100%; margin-bottom: 10px; }

        /* Compact Select/Create section */
        .compact-flex {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .compact-flex > div {
            flex: 1;
            min-width: 180px;
        }
        .compact-box {
            border-radius: 4px;
            background: #fff;
            font-size: 0.9em;
        }
        .paste-area {
            height: 60px; 
            padding: 6px; 
            border: 1px solid #ccc; 
            border-radius: 4px; 
            background: #fff; 
            font-size: 0.9em; 
            overflow-y: auto;
            outline: none;
        }
        #dropZone {
            height: 60px; 
            border: 2px dashed #aaa; 
            border-radius: 4px; 
            background: #f2f2f2; 
            text-align: center; 
            line-height: 58px; 
            font-size: 0.9em; 
            user-select: none;
        }

        .section h2 {
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <h1>DLP File Upload Tester</h1>

    <div class="section">
        <h2>1. Select or Create a File</h2>
        <div class="compact-flex">
            <!-- File Input -->
            <div>
                <label><strong>Choose file:</strong></label><br>
                <input type="file" id="fileInput" />
            </div>

            <!-- Fake File Generator -->
            <div>
                <label><strong>Generate:</strong></label><br>
                <button onclick="generateFakeFile()" style="width: 100%;">Generate Fake File</button>
            </div>

            <!-- Clipboard Paste -->
            <div>
                <label><strong>Paste:</strong></label><br>
                <div id="pasteArea" class="paste-area" contenteditable="true" onpaste="handlePaste(event)">
                    Ctrl+V here
                </div>
            </div>

            <!-- Drag and Drop -->
            <div>
                <label><strong>Drop file:</strong></label><br>
                <div id="dropZone">
                    Drop here
                </div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>2. Send File Using Different Methods</h2>
        <button onclick="uploadFile('POST', 'form')">Form POST</button>
        <button onclick="uploadFile('PUT', 'form')">Form PUT</button>
        <button onclick="uploadFile('PATCH', 'form')">Form PATCH</button>
        <button onclick="uploadViaXHR('POST')">XHR POST</button>
        <button onclick="uploadViaXHR('PUT')">XHR PUT</button>
        <button onclick="sendAsBase64()">Send as Base64 (JSON)</button>
        <button onclick="sendDeleteRequest()">DELETE (no file)</button>
    </div>

    <script>
        let currentFile = null;

        function generateFakeFile() {
            const content = "Dummy data: Card 4111-1111-1111-1111";
            const blob = new Blob([content], { type: 'text/plain' });
            currentFile = new File([blob], "generated_file.txt");
            alert("Fake file generated.");
        }

        function handlePaste(event) {
            const items = (event.clipboardData || window.clipboardData).items;
            for (let item of items) {
                if (item.kind === 'file') {
                    currentFile = item.getAsFile();
                    alert("File pasted and selected.");
                } else if (item.kind === 'string') {
                    item.getAsString(text => {
                        const blob = new Blob([text], { type: 'text/plain' });
                        currentFile = new File([blob], 'clipboard.txt');
                        alert("Text pasted and converted to file.");
                    });
                }
            }
        }

        const dropZone = document.getElementById('dropZone');
        dropZone.ondragover = e => e.preventDefault();
        dropZone.ondrop = e => {
            e.preventDefault();
            currentFile = e.dataTransfer.files[0];
            alert("File dropped and selected.");
        };

        document.getElementById('fileInput').addEventListener('change', function() {
            currentFile = this.files[0];
            alert("File selected via input.");
        });

        function uploadFile(method, sourceTag) {
            if (!currentFile && method !== 'DELETE') {
                alert('No file selected');
                return;
            }
            const formData = new FormData();
            if (method !== 'DELETE') {
                const renamedFile = new File([currentFile], `${method}_${sourceTag}_${currentFile.name}`);
                formData.append('file', renamedFile);
            }
            fetch('/upload', { method: method, body: method === 'DELETE' ? null : formData })
                .then(response => response.json())
                .then(data => alert(JSON.stringify(data)))
                .catch(err => alert('Error: ' + err));
        }

        function uploadViaXHR(method) {
            if (!currentFile) return alert('No file selected');
            const xhr = new XMLHttpRequest();
            const formData = new FormData();
            const renamedFile = new File([currentFile], `${method}_xhr_${currentFile.name}`);
            formData.append('file', renamedFile);
            xhr.open(method, '/upload', true);
            xhr.onload = () => alert('XHR: ' + xhr.responseText);
            xhr.send(formData);
        }

        function sendAsBase64() {
            if (!currentFile) return alert('No file selected');
            const reader = new FileReader();
            reader.onload = function () {
                // btoa expects binary string so reader.readAsBinaryString is used
                const base64 = btoa(reader.result);
                fetch('/upload_json', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename: 'json_' + currentFile.name, data: base64 })
                }).then(r => r.json()).then(data => alert(JSON.stringify(data)));
            };
            reader.readAsBinaryString(currentFile);
        }

        function sendDeleteRequest() {
            fetch('/upload', { method: 'DELETE' })
                .then(res => res.json()).then(data => alert(JSON.stringify(data)));
        }
    </script>
</body>
</html>
    ''')

@app.route('/upload', methods=['POST', 'PUT', 'PATCH', 'DELETE'])
def upload():
    if request.method == 'DELETE':
        return jsonify({'message': 'DELETE received. No file handled.'})
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    return jsonify({'message': f'File uploaded via {request.method}', 'filename': file.filename})

@app.route('/upload_json', methods=['POST'])
def upload_json():
    data = request.get_json()
    filename = data.get('filename', 'unnamed_json.txt')
    filedata = base64.b64decode(data['data'])
    with open(os.path.join(UPLOAD_FOLDER, filename), 'wb') as f:
        f.write(filedata)
    return jsonify({'message': 'File uploaded via JSON', 'filename': filename})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
