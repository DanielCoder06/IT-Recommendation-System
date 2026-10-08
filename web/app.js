const dashboardData = {
  rawJobs: 375,
  itJobs: 72,
  databaseJobs: 291,
};

const demoJobs = [
  {
    title: "Backend Developer",
    company: "Example Company",
    location: "Remote",
    score: 0.82,
  },
  {
    title: "Software Engineer",
    company: "Tech Company",
    location: "Ho Chi Minh City",
    score: 0.78,
  },
  {
    title: "Data Engineer",
    company: "Data Company",
    location: "Da Nang",
    score: 0.74,
  },
];

const rawJobsElement = document.getElementById("raw-jobs");
const itJobsElement = document.getElementById("it-jobs");
const databaseJobsElement = document.getElementById("db-jobs");

const cvFileElement = document.getElementById("cv-file");
const analyzeButton = document.getElementById("analyze-btn");
const resultsElement = document.getElementById("results");

function loadDashboard() {
  rawJobsElement.textContent = dashboardData.rawJobs;
  itJobsElement.textContent = dashboardData.itJobs;
  databaseJobsElement.textContent = dashboardData.databaseJobs;
}

function renderResults(jobs) {
  resultsElement.innerHTML = "";

  jobs.forEach((job, index) => {
    const jobCard = document.createElement("div");

    jobCard.className = "job-card";

    jobCard.innerHTML = `
            <h3>#${index + 1} ${job.title}</h3>
            <p>${job.company}</p>
            <p>${job.location}</p>
            <p class="job-score">
                Matching Score: ${(job.score * 100).toFixed(1)}%
            </p>
        `;

    resultsElement.appendChild(jobCard);
  });
}

function analyzeCV() {
  const file = cvFileElement.files[0];

  if (!file) {
    alert("Vui lòng chọn CV trước.");
    return;
  }

  if (file.type !== "application/pdf") {
    alert("CV phải là file PDF.");
    return;
  }

  resultsElement.innerHTML = `
        <p class="empty-message">
            Analyzing CV...
        </p>
    `;

  setTimeout(() => {
    renderResults(demoJobs);
  }, 800);
}

cvFileElement.addEventListener("change", () => {
  const file = cvFileElement.files[0];

  if (!file) {
    return;
  }

  console.log("Selected CV:", file.name);
});

analyzeButton.addEventListener("click", analyzeCV);

loadDashboard();
