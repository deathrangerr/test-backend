rom flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import openai  # Import the correct module
from urllib.parse import urljoin

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

openai.api_key = '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'

# @app.route('/')
# def index():
#     return render_template('index.html')

@app.route('/get_data', methods=['POST'])
def get_data():
    data = request.get_json()
    url = data['url']

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        return jsonify({"error": f"HTTP Error: {errh}"}), 400
    except requests.exceptions.ConnectionError as errc:
        return jsonify({"error": f"Error Connecting: {errc}"}), 400
    except requests.exceptions.Timeout as errt:
        return jsonify({"error": f"Timeout Error: {errt}"}), 400
    except requests.exceptions.RequestException as err:
        return jsonify({"error": f"An error occurred: {err}"}), 400

    soup = BeautifulSoup(response.text, 'html.parser')
    paragraphs = soup.find_all('p')
    content = "\n".join([p.get_text() for p in paragraphs])

    user_question = data['question']
    chatgpt_response = generate_chatgpt_response(user_question, content)

    linked_content = collect_linked_content(url, content)

    return jsonify({"content": content, "chatgpt_response": chatgpt_response, "linked_content": linked_content})

def generate_chatgpt_response(question, content):
    # prompt = f"Context: {content}\nQuestion: {question}\nAnswer:"

    # response = openai.Completion.create(
    #     engine="text-davinci-003",
    #     prompt=prompt,
    #     temperature=0.7,
    #     max_tokens=2000
    # )

    # return response.choices[0].text.strip()

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": question},
        {"role": "assistant", "content": content}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.2,
        max_tokens=1000,
        frequency_penalty=0.0
    )

    # Extract the assistant's reply
    assistant_reply = response.choices[0].message['content'].strip()

    return assistant_reply


def collect_linked_content(base_url, content):
    linked_content = []

    soup = BeautifulSoup(content, 'html.parser')
    links = soup.find_all('a', href=True)

    for link in links:
        absolute_url = urljoin(base_url, link['href'])
        try:
            linked_response = requests.get(absolute_url)
            linked_response.raise_for_status()
            linked_soup = BeautifulSoup(linked_response.text, 'html.parser')
            linked_paragraphs = linked_soup.find_all('p')
            linked_text = "\n".join([p.get_text() for p in linked_paragraphs])
            linked_content.append({"url": absolute_url, "content": linked_text})
        except requests.exceptions.RequestException as err:
            linked_content.append({"url": absolute_url, "error": f"An error occurred: {err}"})

    return linked_content

if __name__ == '__main__':
    app.run(debug=True)
