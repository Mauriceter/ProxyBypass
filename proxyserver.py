from flask import Flask, request, Response, session, redirect, render_template_string
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = 'super-secret-key'

HTML_TEMPLATE = """
<!doctype html>
<title>Simple Proxy</title>
<h1>Enter Target URL</h1>
<form method="POST">
  <input name="target" placeholder="https://example.com" style="width: 300px;">
  <button type="submit">Start Proxy</button>
</form>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['target'].strip().rstrip('/')
        if not url.startswith('http'):
            url = 'http://' + url
        session['target'] = url
        return redirect('/proxy/')
    return render_template_string(HTML_TEMPLATE)

@app.route('/proxy/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
@app.route('/proxy/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def proxy(path):
    target_base = session.get('target')
    if not target_base:
        return redirect('/')

    target_parsed = urlparse(target_base)
    target_domain = target_parsed.netloc.lower()
    target_url = urljoin(target_base + '/', path)

    # Forward the request to the target
    resp = requests.request(
        method=request.method,
        url=target_url,
        headers={k: v for k, v in request.headers if k.lower() != 'host'},
        cookies=request.cookies,
        data=request.get_data(),
        allow_redirects=False,
        stream=True
    )

    headers = {}
    content = resp.content
    content_type = resp.headers.get('Content-Type', '')

    # Handle 3xx redirects
    if 300 <= resp.status_code < 400:
        location = resp.headers.get('Location')
        if location:
            parsed_location = urlparse(location)
            redirect_domain = parsed_location.netloc.lower()

            # External redirect
            if redirect_domain and redirect_domain != target_domain:
                return f"<h2>Redirected to external website: {location}</h2>", 200

            # Internal redirect — rewrite
            new_path = urljoin('/proxy/', parsed_location.path.lstrip('/'))
            if parsed_location.query:
                new_path += '?' + parsed_location.query
            headers['Location'] = new_path

    # Rewrite internal HTML links
    if 'text/html' in content_type:
        soup = BeautifulSoup(content, 'html.parser')

        for tag in soup.find_all(['a', 'link', 'script', 'img', 'form', 'iframe']):
            attr = 'href' if tag.name in ['a', 'link'] else 'src' if tag.name in ['script', 'img', 'iframe'] else 'action'
            if tag.has_attr(attr):
                original = tag[attr]
                parsed = urlparse(original)

                # Absolute to target domain or relative
                if (not parsed.netloc) or (parsed.netloc.lower() == target_domain):
                    path = parsed.path
                    if parsed.query:
                        path += '?' + parsed.query
                    tag[attr] = urljoin('/proxy/', path.lstrip('/'))

        content = str(soup).encode('utf-8')

    # Pass remaining headers
    for k, v in resp.headers.items():
        if k.lower() not in ['content-encoding', 'content-length', 'transfer-encoding', 'connection', 'location']:
            headers[k] = v

    return Response(content, status=resp.status_code, headers=headers)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
