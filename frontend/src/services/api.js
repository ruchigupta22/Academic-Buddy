import axios from "axios";
const BASE= "/api/v1";

const api= axios.create({
    baseURL: BASE,
    timeout: 120000,
});

export const uploadLecture= (file, courseCode, onProgress)=>{
    const form= new FormData();
    form.append("file", file);
    form.append("course_code", courseCode);
    return api.post("/upload/lecture", form, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e)=> onProgress?.(Math.round((e.loaded/e.total)*100)),

    });
};

export const uploadPYQ = (file, courseCode, year) => {
  const form = new FormData();
  form.append("file", file);
  form.append("course_code", courseCode);
  if (year) form.append("year", year);
  return api.post("/pyq/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 180000,
  });
};

export const sendChat= (question, courseCode)=>
  api.post("/chat", { question, course_code: courseCode });

export const generateQuiz = (courseCode, topic, questionTypes, countPerType, difficulty) =>
  api.post("/quiz/generate", {
    course_code: courseCode,
    topic,
    question_types: questionTypes,
    count_per_type: countPerType,
    difficulty,
  });

export const checkAnswer = (question, questionType, modelAnswer, studentAnswer, marks) =>
  api.post("/quiz/check", {
    question,
    question_type: questionType,
    model_answer: modelAnswer,
    student_answer: studentAnswer,
    marks,
  });

export const askPYQ = (question, courseCode) =>
  api.post("/pyq/ask", { question, course_code: courseCode });
 
export const getPYQReport = (courseCode) =>
  api.get("/pyq/report", { params: { course_code: courseCode } });
 
export const getPYQAnalytics = (courseCode) =>
  api.get("/pyq/analytics", { params: { course_code: courseCode } });

export const getPriorityTopics = (courseCode, daysLeft) =>
  api.get("/revision/priority", { params: { course_code: courseCode, days_left: daysLeft } });
 
export const getStudyPlan = (courseCode, daysLeft, hoursPerDay) =>
  api.get("/revision/plan", {
    params: { course_code: courseCode, days_left: daysLeft, hours_per_day: hoursPerDay },
  });
 
export const getFormulaSheet = (courseCode) =>
  api.get("/revision/formula-sheet", { params: { course_code: courseCode } });
 
export const getConfusedConcepts = (courseCode) =>
  api.get("/revision/confused", { params: { course_code: courseCode } });
 
export const getRevisionNotes = (courseCode, topic) =>
  api.get("/revision/notes", { params: { course_code: courseCode, topic } });
export const initUser = (username, courseCode) =>
  api.post("/profile/init", { username, course_code: courseCode });
 
export const getProfileSummary = (username, courseCode) =>
  api.get("/profile/summary", { params: { username, course_code: courseCode } });
 
export const getRecommendations = (username, courseCode) =>
  api.get("/profile/recommendations", { params: { username, course_code: courseCode } });
 
export const getAIMessage = (username, courseCode) =>
  api.get("/profile/ai-message", { params: { username, course_code: courseCode } });
 
export const saveQuiz = (username, courseCode, topic, difficulty, questions, results) =>
  api.post("/profile/save-quiz", {
    username, course_code: courseCode, topic, difficulty, questions,
    results: Object.fromEntries(Object.entries(results).map(([k, v]) => [String(k), v])),
  });
 
export const saveChat = (username, courseCode, question, answer) =>
  api.post("/profile/save-chat", { username, course_code: courseCode, question, answer });
 
export const getTopicAccuracy = (username, courseCode) =>
  api.get("/profile/accuracy", { params: { username, course_code: courseCode } });
 
export const getQuizHistory = (username, courseCode) =>
  api.get("/profile/history", { params: { username, course_code: courseCode } });
