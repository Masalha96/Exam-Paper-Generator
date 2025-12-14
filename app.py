from flask import Flask, render_template_string, request, send_file, send_from_directory
from io import BytesIO
import zipfile
import random

def parse_questions(text):
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
    questions = []
    i = 0
    while i < len(lines):
        if lines[i].startswith('Q'):
            q_text = lines[i]
            choices = []
            i += 1
            while i < len(lines) and len(choices) < 4:
                if lines[i] and lines[i][0] in 'ABCD' and ')' in lines[i]:
                    choices.append(lines[i])
                    i += 1
                else:
                    break
            if len(choices) == 4:
                questions.append({'question': q_text, 'choices': choices})
        else:
            i += 1
    return questions

def parse_answers(text):
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
    answers = []
    for line in lines:
        for char in line.upper():
            if char in 'ABCD':
                answers.append(char)
                break
    return answers

def shuffle_exam(questions, answers):
    paired = list(zip(questions, answers))
    random.shuffle(paired)
    new_questions = []
    new_answers = []
    for q, correct_letter in paired:
        # Get the choice texts without letters
        choice_texts = [c.split(')', 1)[1].strip() for c in q['choices']]
        # Find which text is correct
        correct_idx = ord(correct_letter) - ord('A')
        correct_text = choice_texts[correct_idx]
        # Shuffle the choice texts
        random.shuffle(choice_texts)
        # Find new position of correct answer
        new_correct_idx = choice_texts.index(correct_text)
        new_correct_letter = chr(ord('A') + new_correct_idx)
        # Rebuild choices with A), B), C), D) labels
        new_choices = [f"{chr(65+i)}) {text}" for i, text in enumerate(choice_texts)]
        new_questions.append({'question': q['question'], 'choices': new_choices})
        new_answers.append(new_correct_letter)
    return new_questions, new_answers

def generate_all(questions, answers, num_versions):
    files = {}
    for i in range(num_versions):
        version = chr(65 + i)
        shuffled_q, shuffled_a = shuffle_exam(questions, answers)
        exam_text = f"EXAM VERSION {version}\n{'='*50}\n\n"
        for idx, q in enumerate(shuffled_q, 1):
            q_text = q['question']
            if ':' in q_text:
                q_text = q_text.split(':', 1)[1].strip()
            exam_text += f"{idx}. {q_text}\n"
            for choice in q['choices']:
                exam_text += f"   {choice}\n"
            exam_text += "\n"
        files[f'exam_version_{version}.txt'] = exam_text
        answer_text = f"ANSWER KEY - VERSION {version}\n{'='*50}\n\n"
        for idx, ans in enumerate(shuffled_a, 1):
            answer_text += f"{idx}. {ans}\n"
        files[f'answers_version_{version}.txt'] = answer_text
    return files

app = Flask(__name__)

@app.route('/img/<path:filename>')
def serve_image(filename):
    return send_from_directory('img', filename)

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Exam Generator - Philistine Group</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#f8f9fa;--card:#fff;--text:#1f2937;--light:#6b7280;--primary:#667eea;--border:#e5e7eb;--shadow:rgba(0,0,0,0.1);--up-bg:#fafafa;--up-border:#e5e7eb;--up-hover:#f0f4ff;--success:#10b981;--success-light:rgba(16,185,129,0.1)}
body.dark{--bg:#0f172a;--card:#1e293b;--text:#f1f5f9;--light:#cbd5e1;--border:#334155;--shadow:rgba(0,0,0,0.3);--up-bg:#1e293b;--up-border:#334155;--up-hover:#334155;--success:#10b981;--success-light:rgba(16,185,129,0.15)}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;padding:0;transition:all .3s}
.theme-toggle{position:absolute;top:25px;right:25px;padding:12px 20px;background:var(--card);border:2px solid var(--border);border-radius:14px;cursor:pointer;display:flex;align-items:center;gap:10px;font-size:14px;font-weight:700;color:var(--text);transition:all .3s;box-shadow:0 4px 20px var(--shadow);z-index:10}
.theme-toggle::before{content:'';position:absolute;inset:0;border-radius:14px;padding:2px;background:linear-gradient(135deg,#667eea,#764ba2);-webkit-mask:linear-gradient(#fff 0 0) content-box,linear-gradient(#fff 0 0);mask:linear-gradient(#fff 0 0) content-box,linear-gradient(#fff 0 0);-webkit-mask-composite:xor;mask-composite:exclude;opacity:0;transition:opacity .3s}
.theme-toggle:hover::before{opacity:1}
.theme-toggle:hover{transform:translateY(-2px) scale(1.02);box-shadow:0 6px 30px var(--shadow)}
.header{position:sticky;top:0;background:var(--bg);z-index:100;padding:25px 20px;border-bottom:1px solid var(--border);box-shadow:0 4px 20px var(--shadow);backdrop-filter:blur(10px)}
.container{max-width:680px;width:100%;margin:0 auto}
.main-content{padding:20px}
.logo-section{display:flex;align-items:center;gap:20px;margin-bottom:16px;padding:10px 0}
.logo{width:140px;height:140px;flex-shrink:0;position:relative}
.logo img{width:100%;height:100%;object-fit:contain;filter:drop-shadow(0 6px 20px rgba(102,126,234,.5));transition:transform .3s}
.logo:hover img{transform:scale(1.05) rotate(5deg)}
body.dark .logo img{filter:drop-shadow(0 4px 16px rgba(102,126,234,.6)) brightness(1.1)}
.logo-text{flex:1;text-align:left;display:flex;flex-direction:column;justify-content:center}
h1{font-size:26px;font-weight:800;margin-bottom:6px;letter-spacing:-0.5px;line-height:1.2;background:linear-gradient(135deg,#667eea,#764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.subtitle{font-size:13px;color:var(--light);font-weight:600;letter-spacing:0.3px;line-height:1.4}
.developers{font-size:11.5px;color:var(--light);font-weight:500;margin-top:4px;opacity:0.85}
.dev-name{color:var(--primary);font-weight:600}
.progress{display:flex;justify-content:space-between;align-items:center;position:relative;margin:20px 0 0;padding:0 30px}
.progress::before{content:'';position:absolute;top:17px;left:25px;right:25px;height:3px;background:var(--border);z-index:0}
.progress-line{position:absolute;top:17px;left:25px;height:3px;background:linear-gradient(90deg,#667eea,#764ba2);width:0;transition:width .5s;z-index:1;box-shadow:0 0 10px rgba(102,126,234,.5)}
.step{position:relative;z-index:2;display:flex;flex-direction:column;align-items:center;flex:1}
.step-circle{width:32px;height:32px;border-radius:50%;background:var(--card);border:2.5px solid var(--border);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:13px;color:var(--light);transition:all .3s;margin-bottom:5px}
.step.active .step-circle{background:linear-gradient(135deg,#667eea,#764ba2);border-color:#667eea;color:#fff;transform:scale(1.1);box-shadow:0 4px 15px rgba(102,126,234,.4)}
.step.completed .step-circle{background:#10b981;border-color:#10b981;color:#fff}
.step-label{font-size:12px;font-weight:600;color:var(--light);transition:color .3s}
.step.active .step-label,.step.completed .step-label{color:var(--text)}
.card{background:var(--card);border-radius:18px;padding:24px;box-shadow:0 8px 35px var(--shadow);border:1px solid var(--border);margin-bottom:15px}
.wizard-content{min-height:600px;position:relative;overflow:hidden}
.slide{position:absolute;top:0;left:0;width:100%;opacity:0;transform:translateX(100px);transition:all .5s;pointer-events:none}
.slide.active{opacity:1;transform:translateX(0);pointer-events:auto}
.slide.prev{opacity:0;transform:translateX(-100px)}
.slide-header{margin-bottom:14px}
.slide-title{font-size:22px;font-weight:800;margin-bottom:8px;color:var(--primary)}
.slide-desc{font-size:13.5px;color:var(--light);line-height:1.6}
.upload-box{border:2.5px dashed var(--up-border);border-radius:16px;padding:24px 20px 26px;text-align:center;cursor:pointer;background:var(--up-bg);transition:all .3s;margin:0 0 20px 0}
.upload-box:hover{border-color:var(--primary);background:var(--up-hover);transform:translateY(-3px);box-shadow:0 8px 25px rgba(102,126,234,.15)}
.upload-box.uploading{border-color:var(--primary);background:var(--up-hover);border-style:solid}
.upload-box.uploaded{border-style:solid;border-color:var(--success);background:var(--success-light)}
.upload-icon{font-size:36px;margin-bottom:10px;opacity:.75}
.upload-box.uploaded .upload-icon{opacity:1}
.upload-text{font-size:15px;font-weight:700;color:var(--text);margin-bottom:6px}
.upload-box.uploading .upload-text{color:var(--primary);font-weight:600}
.upload-box.uploaded .upload-text{color:var(--success)}
.upload-hint{font-size:11.5px;color:var(--light);font-weight:500}
input[type=file]{display:none}
.number-selector{display:flex;align-items:center;justify-content:center;gap:20px;margin:25px 0}
.num-btn{width:54px;height:54px;border:none;border-radius:13px;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;font-size:28px;font-weight:700;cursor:pointer;transition:all .3s;box-shadow:0 4px 15px rgba(102,126,234,.3);display:flex;align-items:center;justify-content:center}
.num-btn:hover{transform:scale(1.1);box-shadow:0 6px 20px rgba(102,126,234,.5)}
.num-btn:active{transform:scale(.95)}
.num-display{width:110px;height:70px;background:var(--up-bg);border:2.5px solid var(--border);border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:42px;font-weight:800;color:var(--primary);box-shadow:inset 0 2px 8px var(--shadow)}
.num-label{text-align:center;margin-top:15px;font-size:14px;color:var(--light);font-weight:500}
.summary-box{background:var(--up-bg);border:2px solid var(--border);border-radius:14px;padding:14px;margin:14px 0}
.summary-item{display:flex;align-items:center;gap:8px;padding:9px;margin-bottom:7px;background:var(--card);border-radius:10px;border:1px solid var(--border)}
.summary-item:last-child{margin-bottom:0}
.summary-icon{font-size:20px;flex-shrink:0}
.summary-content{flex:1;min-width:0}
.summary-label{font-size:10px;font-weight:700;color:var(--light);text-transform:uppercase;letter-spacing:.5px}
.summary-value{font-size:14px;font-weight:700;color:var(--text);margin-top:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.nav-buttons{display:flex;gap:10px;margin-top:20px}
.btn{flex:1;padding:14px;border:none;border-radius:11px;font-size:15px;font-weight:700;cursor:pointer;transition:all .3s;display:flex;align-items:center;justify-content:center;gap:8px}
.btn-back{background:var(--card);color:var(--text);border:2px solid var(--border);box-shadow:0 4px 12px var(--shadow)}
.btn-back:hover{background:var(--up-hover);transform:translateY(-2px)}
.btn-next,.btn-generate{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;box-shadow:0 6px 20px rgba(102,126,234,.4)}
.btn-next:hover,.btn-generate:hover{transform:translateY(-3px);box-shadow:0 8px 30px rgba(102,126,234,.5)}
.btn:disabled{opacity:.5;cursor:not-allowed;transform:none!important}

@media(max-width:768px){.header{padding:20px 15px}.logo-section{flex-direction:row;gap:15px}.logo{width:60px;height:60px}.logo-text{text-align:left}h1{font-size:20px}.subtitle{font-size:11px}.developers{font-size:10px}.progress{padding:0 15px}.step-label{font-size:10px}.card{padding:18px}.main-content{padding:15px}.theme-toggle{top:15px;right:15px;padding:10px 16px;font-size:13px}}
.code-example{font-family:'Courier New',monospace;background:#1f2937;color:#10b981;padding:12px;border-radius:10px;font-size:11.5px;line-height:1.7;box-shadow:inset 0 1px 3px rgba(0,0,0,0.3)}
body.dark .code-example{background:#0f172a;color:#22c55e}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes uploadSpin{0%{transform:rotate(0deg) scale(1)}50%{transform:rotate(180deg) scale(1.15)}100%{transform:rotate(360deg) scale(1)}}
@keyframes uploadSuccess{0%{transform:scale(0.8);opacity:0.5}50%{transform:scale(1.2)}100%{transform:scale(1);opacity:1}}
.upload-box.uploading .upload-icon{animation:uploadSpin 0.6s cubic-bezier(0.68,-0.55,0.265,1.55) infinite}
.upload-box.uploaded .upload-icon{animation:uploadSuccess 0.4s cubic-bezier(0.34,1.56,0.64,1)}
</style>
</head>
<body>
<div class="header">
<div class="container">
<div class="theme-toggle" onclick="toggleTheme()">
<span id="themeText">Light</span>
</div>
<div class="logo-section">
<div class="logo"><img src="/img/logo.png" alt="Exam Generator"></div>
<div class="logo-text">
<h1>Exam Paper Generator</h1>
<p class="subtitle">Near East University | AII102 | Philistine Group</p>
<p class="developers">Developed by <span class="dev-name">Said A S</span> & <span class="dev-name">Yousef Hussein</span></p>
</div>
</div>
<div class="progress">
<div class="progress-line" id="progLine"></div>
<div class="step active" id="step1"><div class="step-circle">1</div><div class="step-label">Questions</div></div>
<div class="step" id="step2"><div class="step-circle">2</div><div class="step-label">Answers</div></div>
<div class="step" id="step3"><div class="step-circle">3</div><div class="step-label">Versions</div></div>
<div class="step" id="step4"><div class="step-circle">4</div><div class="step-label">Review</div></div>
</div>
</div>
<div class="main-content">
<div class="container">
<form id="form" method="post" enctype="multipart/form-data">
<div class="card">
<div class="wizard-content">
<div class="slide active" id="slide1">
<div class="slide-header">
<div class="slide-title">📄 Step 1: Prepare Your Questions</div>
<div class="slide-desc">Create a text file with your exam questions. Follow the format below exactly - each question needs a number (Q1:, Q2:) and exactly four choices (A, B, C, D).</div>
</div>
<div style="background:linear-gradient(135deg,rgba(102,126,234,0.08),rgba(118,75,162,0.08));border:1px solid var(--primary);border-radius:12px;padding:12px;margin-bottom:20px">
<div style="font-weight:700;margin-bottom:10px;color:var(--primary);font-size:13px;display:flex;align-items:center;gap:6px">
<span>📋</span><span>Required Format:</span>
</div>
<div class="code-example">
Q1: What is the capital of France?<br>
A) London<br>
B) Paris<br>
C) Berlin<br>
D) Madrid<br>
<br>
Q2: What is 2 + 2?<br>
A) 3<br>
B) 4<br>
C) 5<br>
D) 6
</div>
<div style="margin-top:8px;color:var(--light);font-size:11px;line-height:1.5;padding-left:4px">✅ Start with Q1:, Q2:, Q3:... | ✅ Exactly 4 choices: A), B), C), D)</div>
</div>
<div class="upload-box" id="upBox1" onclick="document.getElementById('qFile').click()">
<div class="upload-icon">📤</div>
<div class="upload-text" id="upText1">Click to upload your questions file</div>
<div class="upload-hint">Upload a .txt file formatted as shown above</div>
</div>
<input type="file" id="qFile" name="questions" accept=".txt" onchange="fileUp(1)">
</div>
<div class="slide" id="slide2">
<div class="slide-header">
<div class="slide-title">✅ Step 2: Prepare Your Answer Key</div>
<div class="slide-desc">Create a text file with the correct answers. Each line should have the question number followed by the correct answer letter.</div>
</div>
<div style="background:linear-gradient(135deg,rgba(102,126,234,0.08),rgba(118,75,162,0.08));border:1px solid var(--primary);border-radius:12px;padding:12px;margin-bottom:20px">
<div style="font-weight:700;margin-bottom:10px;color:var(--primary);font-size:13px;display:flex;align-items:center;gap:6px">
<span>📋</span><span>Required Format:</span>
</div>
<div class="code-example">
Q1: C<br>
Q2: B<br>
Q3: A<br>
Q4: D
</div>
<div style="margin-top:8px;color:var(--light);font-size:11px;line-height:1.5;padding-left:4px">✅ Match question numbers | ✅ Use only: A, B, C, or D</div>
</div>
<div class="upload-box" id="upBox2" onclick="document.getElementById('aFile').click()">
<div class="upload-icon">📤</div>
<div class="upload-text" id="upText2">Click to upload your answer key file</div>
<div class="upload-hint">Upload a .txt file formatted as shown above</div>
</div>
<input type="file" id="aFile" name="answers" accept=".txt" onchange="fileUp(2)">
</div>
<div class="slide" id="slide3">
<div class="slide-header">
<div class="slide-title">🔢 Step 3: Choose Number of Versions</div>
<div class="slide-desc">Select how many unique exam versions to generate. Each version will have shuffled questions and answer choices to prevent cheating.</div>
</div>
<div class="number-selector">
<button type="button" class="num-btn" onclick="chgNum(-1)">−</button>
<div class="num-display" id="numDisp">2</div>
<button type="button" class="num-btn" onclick="chgNum(1)">+</button>
</div>
<input type="hidden" id="numVer" name="num_versions" value="2">
<div class="num-label">✨ Each version gets unique question order and shuffled choices | 🔒 Perfect for preventing cheating</div>
</div>
<div class="slide" id="slide4">
<div class="slide-header">
<div class="slide-title">🎯 Step 4: Review & Generate</div>
<div class="slide-desc">Double-check your files and settings below, then click Generate to create your exam papers and answer keys in a ZIP file.</div>
</div>
<div class="summary-box">
<div class="summary-item">
<div class="summary-icon">📄</div>
<div class="summary-content">
<div class="summary-label">Questions File</div>
<div class="summary-value" id="sumQ">Not uploaded</div>
</div>
</div>
<div class="summary-item">
<div class="summary-icon">✅</div>
<div class="summary-content">
<div class="summary-label">Answers File</div>
<div class="summary-value" id="sumA">Not uploaded</div>
</div>
</div>
<div class="summary-item">
<div class="summary-icon">🔢</div>
<div class="summary-content">
<div class="summary-label">Number of Versions</div>
<div class="summary-value" id="sumN">2 versions (A, B)</div>
</div>
</div>
</div>
</div>
</div>
<div class="nav-buttons">
<button type="button" class="btn btn-back" id="btnBack" onclick="prev()" style="display:none"><span>←</span><span>Back</span></button>
<button type="button" class="btn btn-next" id="btnNext" onclick="next()" disabled><span>Next</span><span>→</span></button>
<button type="submit" class="btn btn-generate" id="btnGen" style="display:none"><span>✨</span><span>Generate</span></button>
</div>
</div>
</form>

</div>
</div>
<script>
let step=1,hasQ=false,hasA=false,qName='',aName='',numV=2;
function toggleTheme(){const d=document.body.classList.toggle('dark'),t=document.getElementById('themeText');if(d){t.textContent='Dark';localStorage.theme='dark'}else{t.textContent='Light';localStorage.theme='light'}}
if(localStorage.theme==='dark'){document.body.classList.add('dark');document.getElementById('themeText').textContent='Dark'}
function fileUp(s){const f=document.getElementById(s===1?'qFile':'aFile'),b=document.getElementById('upBox'+s),t=document.getElementById('upText'+s);if(f.files&&f.files[0]){b.classList.add('uploading');t.textContent='⏳ Uploading...';setTimeout(()=>{const n=f.files[0].name;b.classList.remove('uploading');b.classList.add('uploaded');t.textContent='✓ '+n;if(s===1){hasQ=true;qName=n}else{hasA=true;aName=n}chkNext()},500)}}
function chkNext(){const btn=document.getElementById('btnNext');btn.disabled=!((step===1&&hasQ)||(step===2&&hasA)||(step===3))}
function chgNum(d){numV=Math.max(2,Math.min(26,numV+d));document.getElementById('numDisp').textContent=numV;document.getElementById('numVer').value=numV;updSum();chkNext()}
function updSum(){document.getElementById('sumQ').textContent=qName||'Not uploaded';document.getElementById('sumA').textContent=aName||'Not uploaded';const v=Array.from({length:numV},(_,i)=>String.fromCharCode(65+i)).join(', ');document.getElementById('sumN').textContent=numV+' versions ('+v+')'}
function updProg(){const p=document.getElementById('progLine');p.style.width=((step-1)/3*100)+'%';for(let i=1;i<=4;i++){const e=document.getElementById('step'+i);e.classList.remove('active','completed');if(i<step)e.classList.add('completed');else if(i===step)e.classList.add('active')}}
function next(){if(step<4){document.getElementById('slide'+step).classList.remove('active');document.getElementById('slide'+step).classList.add('prev');step++;const s=document.getElementById('slide'+step);s.classList.remove('prev');s.classList.add('active');updNav();updProg();chkNext();if(step===4)updSum()}}
function prev(){if(step>1){document.getElementById('slide'+step).classList.remove('active','prev');step--;const s=document.getElementById('slide'+step);s.classList.add('active');s.classList.remove('prev');updNav();updProg();chkNext()}}
function updNav(){const back=document.getElementById('btnBack'),next=document.getElementById('btnNext'),gen=document.getElementById('btnGen');back.style.display=step>1?'flex':'none';next.style.display=step<4?'flex':'none';gen.style.display=step===4?'flex':'none'}
document.getElementById('form').onsubmit=function(e){e.preventDefault();const btn=document.getElementById('btnGen');btn.innerHTML='<span style="animation:spin 1s linear infinite">⚙️</span><span>Generating...</span>';btn.disabled=true;const formData=new FormData(this);fetch('/',{method:'POST',body:formData}).then(response=>{console.log('Response status:',response.status);if(!response.ok){return response.text().then(txt=>{throw new Error(txt||'Generation failed')})}return response.blob()}).then(blob=>{console.log('Blob size:',blob.size);if(blob.size<100){throw new Error('Invalid file generated')}const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='exam_papers.zip';document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(url);btn.innerHTML='<span>✅</span><span>Success!</span>';btn.style.background='linear-gradient(135deg,#10b981,#059669)';setTimeout(()=>location.reload(),2000)}).catch(err=>{console.error('Error:',err);btn.innerHTML='<span>✨</span><span>Generate</span>';btn.disabled=false;alert('Error: '+err.message)})};
updNav();updProg();
</script>
</body>
</html>'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            q_file = request.files['questions']
            a_file = request.files['answers']
            num = int(request.form['num_versions'])
            
            questions = parse_questions(q_file.read().decode('utf-8'))
            answers = parse_answers(a_file.read().decode('utf-8'))
            
            if not questions:
                return "❌ No questions found. Check your format!", 400
            if len(questions) != len(answers):
                return f"❌ Mismatch: {len(questions)} questions vs {len(answers)} answers", 400
            
            files = generate_all(questions, answers, num)
            
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for name, content in files.items():
                    zf.writestr(name, content.encode('utf-8'))
            
            zip_buffer.seek(0)
            return send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name='exam_papers.zip'
            )
        except Exception as e:
            return f"❌ Error: {str(e)}", 400
    
    return render_template_string(HTML)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎓 EXAM PAPER GENERATOR")
    print("="*60)
    print("🏛️  Near East University")
    print("📚 Course: AII102")
    print("🏆 Group: Philistine Group")
    print("👥 Team: Said AS & Yousef Hussein")
    print("="*60)
    print("🌐 http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, port=5000)
