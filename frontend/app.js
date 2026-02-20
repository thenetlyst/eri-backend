const API = "http://localhost:8000";

let token = null;
let attemptId = null;
let currentQuestion = null;
let order = 1;


// =======================
// LOGIN
// =======================
async function login() {

  const email = document.getElementById("email").value;

  const res = await fetch(API + "/auth/dev-login", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({email})
  });

  const data = await res.json();

  console.log("LOGIN:", data);

  token = data.access_token;

  startAttempt();
}


// =======================
// START ATTEMPT
// =======================
async function startAttempt() {

  const res = await fetch(API + "/attempts/start", {
    method: "POST",
    headers: {
      "Content-Type":"application/json",
      Authorization: "Bearer " + token
    },
    body: JSON.stringify({
      exam_day_id: "72e6dab9-f9e8-4736-97dc-df9def381439"
    })
  });

  const data = await res.json();

  console.log("START ATTEMPT:", data);

  if (!data.attempt_id) {
    alert("Attempt failed — check backend logs");
    return;
  }

  attemptId = data.attempt_id;

  document.getElementById("login").style.display="none";
  document.getElementById("exam").style.display="block";

  loadQuestion();
}


// =======================
// LOAD QUESTION
// =======================
async function loadQuestion() {

  const res = await fetch(
    API + `/attempts/${attemptId}/questions/${order}`,
    { headers: { Authorization: "Bearer " + token } }
  );

  const data = await res.json();

  console.log("QUESTION:", data);

  if (!data || !data.question_text) {
    document.getElementById("question").innerText = "No question";
    document.getElementById("options").innerHTML = "";
    return;
  }

  currentQuestion = data;

  document.getElementById("question").innerText =
    `Q${data.question_order}: ${data.question_text}`;

  renderOptions(data.options);
}


// =======================
// RENDER OPTIONS
// =======================
function renderOptions(options) {

  const container = document.getElementById("options");
  container.innerHTML = "";

  options.forEach(opt => {

    const btn = document.createElement("button");

    btn.innerText = `${opt.key}: ${opt.text}`;

    btn.onclick = () => submitAnswer(opt.key);

    container.appendChild(btn);
    container.appendChild(document.createElement("br"));
  });
}


// =======================
// SUBMIT ANSWER
// =======================
async function submitAnswer(answerKey) {

  await fetch(API + `/attempts/${attemptId}/submit-answer`, {
    method:"POST",
    headers:{
      "Content-Type":"application/json",
      Authorization:"Bearer "+token
    },
    body:JSON.stringify({
      question_id: currentQuestion.question_id,
      selected_option: answerKey,
      hint_used:false
    })
  });

  alert("Answer saved");
}


// =======================
// NAVIGATION
// =======================
function nextQuestion(){
  order++;
  loadQuestion();
}

function prevQuestion(){
  if(order>1){
    order--;
    loadQuestion();
  }
}


// =======================
// FINAL SUBMIT
// =======================
async function finalizeAttempt(){

  await fetch(API + `/attempts/${attemptId}/complete`, {
    method:"POST",
    headers:{ Authorization:"Bearer "+token }
  });

  alert("Exam submitted");
}