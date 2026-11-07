document.addEventListener("DOMContentLoaded", () => {
  // ==================== CÁC HÀM DÙNG CHUNG (HELPER) ====================
  const isValidHttpUrl = (str) => {
    if (!str) return false;
    try {
      return ["http:", "https:"].includes(new URL(str).protocol);
    } catch {
      return false;
    }
  };

  const showPlaceholder = (container, msg, type = "state-loading") => {
    container.innerHTML = `<div class="state-placeholder ${type}">${msg}</div>`;
  };

  // Hàm ẩn/hiện chi tiết Matching (Đã chuyển ra ngoài để có thể gọi từ onclick)
  window.toggleMatchDetails = (index) => {
    const detailsDiv = document.getElementById(`details-${index}`);
    if (detailsDiv) {
      if (detailsDiv.style.display === "none") {
        detailsDiv.style.display = "block";
      } else {
        detailsDiv.style.display = "none";
      }
    }
  };

  // ==================== 1. LOGIC UPLOAD CV (TAB 1) ====================
  const cvForm = document.getElementById("cvForm");
  const cvFileInput = document.getElementById("cvFile");
  const dropZone = document.getElementById("dropZone");
  const dropPrompt = document.getElementById("dropPrompt");
  const fileNameDisplay = document.getElementById("fileNameDisplay");
  const jobsDisplaySection = document.getElementById("jobsDisplaySection");
  const jobsRecommendGrid = document.getElementById("jobsRecommendGrid");
  const recommendCountText = document.getElementById("recommendCountText");

  // --- PHẦN KÉO THẢ FILE ---
  if (dropZone && cvFileInput) {
    ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
      document.body.addEventListener(
        eventName,
        (e) => e.preventDefault(),
        false,
      );
    });

    dropZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropZone.classList.add("dragover");
    });

    dropZone.addEventListener("dragleave", (e) => {
      e.preventDefault();
      dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropZone.classList.remove("dragover");

      const files = e.dataTransfer.files;
      if (files && files.length > 0) {
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(files[0]);
        cvFileInput.files = dataTransfer.files;
        handleFileSelection(files[0]);
      }
    });
  }

  cvFileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) handleFileSelection(e.target.files[0]);
  });

  function handleFileSelection(file) {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      alert("Vui lòng chọn file .pdf");
      cvFileInput.value = "";
      fileNameDisplay.style.display = "none";
      dropPrompt.style.display = "block";
      return;
    }
    dropPrompt.style.display = "none";
    fileNameDisplay.textContent = file.name;
    fileNameDisplay.style.display = "inline-block";
  }

  // --- SUBMIT FORM (GỌI API) ---
  cvForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!cvFileInput.files.length) return alert("Vui lòng chọn file CV!");

    const file = cvFileInput.files[0];
    const submitBtn = document.getElementById("btnSubmitCV");

    submitBtn.disabled = true;
    submitBtn.textContent = "Đang tìm kiếm...";
    jobsDisplaySection.style.display = "block";
    recommendCountText.textContent = `(Đang phân tích CV: ${file.name}...)`;
    showPlaceholder(
      jobsRecommendGrid,
      "Đang phân tích cấu trúc, kỹ năng CV...",
    );

    const formData = new FormData();
    formData.append("file", file);
    formData.append("exclude_senior", "true");
    formData.append("top_k", "10");

    try {
      const res = await fetch("/api/recommend-cv", {
        method: "POST",
        body: formData,
      });
      const resData = await res.json();

      if (!res.ok) throw new Error(resData.detail || "Lỗi phân tích CV");

      recommendCountText.textContent = `(Tìm thấy ${resData.data.length} công việc phù hợp)`;

      if (resData.data.length === 0) {
        return showPlaceholder(
          jobsRecommendGrid,
          "Không tìm thấy công việc phù hợp.",
          "state-empty",
        );
      }

      // --- RENDER KẾT QUẢ ---
      jobsRecommendGrid.innerHTML = resData.data
        .map((job, index) => {
          const link = isValidHttpUrl(job.url)
            ? `<a href="${job.url}" target="_blank" rel="noopener">🔗 Ứng tuyển</a>`
            : "";

          // Xây dựng phần chi tiết (ẩn mặc định)
          let detailsHtml = "";
          let buttonHtml = "";

          if (job._details && job._details.length > 0) {
            const topMatches = job._details.slice(0, 3); // Lấy 3 cặp khớp nhất
            const matchesContent = topMatches
              .map(
                (match) => `
              <div class="match-item">
                  <span class="match-score">Độ tương đồng: ${(match.similarity * 100).toFixed(1)}%</span>
                  <p><strong>[Yêu cầu công việc]</strong> ${match.jd_text}</p>
                  <p><strong>[Bạn đã đáp ứng]</strong> ${match.cv_text}</p>
              </div>
          `,
              )
              .join("");

            detailsHtml = `
              <div class="matching-details" id="details-${index}" style="display: none;">
                  <h4>Chi tiết kết quà tìm kiếm:</h4>
                  ${matchesContent}
              </div>
          `;

            buttonHtml = `<button class="btn-toggle-details" onclick="toggleMatchDetails(${index})">🔍 Xem chi tiết kết quả</button>`;
          }

          return `
              <div class="job-card-item">
                  <div>
                      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                          <div class="job-item-title" style="margin-bottom: 0;">💼 ${job.title}</div>
                          <span class="rank-badge">#${job.rank}</span>
                      </div>
                      <div class="job-item-meta"><strong>🏢 Công ty:</strong> ${job.company}</div>
                      <div class="job-item-meta"><strong>📍 Địa điểm:</strong> ${job.location}</div>
                  </div>
                  ${detailsHtml}
                  <div class="job-item-footer">
                      <div>
                          <span class="status-badge">Đang tuyển</span>
                          ${buttonHtml}
                      </div>
                      ${link}
                  </div>
              </div>
          `;
        })
        .join("");
    } catch (err) {
      showPlaceholder(jobsRecommendGrid, err.message, "state-error");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Tìm kiếm";
    }
  });

  // ==================== 2. LOGIC CHUYỂN TAB & PHÂN TRANG ====================
  const tabRecommend = document.getElementById("tabRecommend");
  const tabAllJobs = document.getElementById("tabAllJobs");
  const pageRecommend = document.getElementById("pageRecommend");
  const pageAllJobs = document.getElementById("pageAllJobs");
  const jobsGrid = document.getElementById("jobsGrid");

  let currentPage = 1,
    totalPages = 1;
  const limit = 9;

  tabRecommend.addEventListener("click", () => {
    tabRecommend.classList.add("active");
    tabAllJobs.classList.remove("active");
    pageRecommend.classList.add("active");
    pageAllJobs.classList.remove("active");
  });

  tabAllJobs.addEventListener("click", () => {
    tabAllJobs.classList.add("active");
    tabRecommend.classList.remove("active");
    pageAllJobs.classList.add("active");
    pageRecommend.classList.remove("active");
    loadJobs(currentPage);
  });

  document.getElementById("btnViewMoreJobs")?.addEventListener("click", () => {
    tabAllJobs.click();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  // Hàm tải danh sách Jobs cho Tab 2
  async function loadJobs(page = 1) {
    showPlaceholder(jobsGrid, `Đang tải dữ liệu (Trang ${page})...`);

    try {
      const res = await fetch(`/api/jobs?page=${page}&limit=${limit}`);
      const data = await res.json();

      totalPages = data.total_pages || 1;
      currentPage = data.page || 1;

      document.getElementById("jobsTotalText").textContent =
        `Tổng cộng: ${data.total} việc làm`;
      document.getElementById("pageInfoText").textContent =
        `Trang ${currentPage} / ${totalPages}`;
      document.getElementById("btnPrevPage").disabled = currentPage <= 1;
      document.getElementById("btnNextPage").disabled =
        currentPage >= totalPages;

      if (data.data.length === 0) {
        return showPlaceholder(
          jobsGrid,
          "Không có công việc nào.",
          "state-empty",
        );
      }

      jobsGrid.innerHTML = data.data
        .map(
          (job) => `
          <div class="job-card-item">
              <div>
                  <div class="job-item-title">💼 ${job.title}</div>
                  <div class="job-item-meta"><strong>🏢 Công ty:</strong> ${job.company}</div>
                  <div class="job-item-meta"><strong>📍 Địa điểm:</strong> ${job.location}</div>
              </div>
              <div class="job-item-footer">
                  <span class="status-badge">Đang tuyển</span>
                  ${isValidHttpUrl(job.url) ? `<a href="${job.url}" target="_blank" rel="noopener">🔗 Xem chi tiết</a>` : ""}
              </div>
          </div>
      `,
        )
        .join("");
    } catch (err) {
      showPlaceholder(jobsGrid, "Lỗi kết nối Server.", "state-error");
    }
  }

  document.getElementById("btnPrevPage").addEventListener("click", () => {
    if (currentPage > 1) loadJobs(currentPage - 1);
  });

  document.getElementById("btnNextPage").addEventListener("click", () => {
    if (currentPage < totalPages) loadJobs(currentPage + 1);
  });

  // ==================== 3. LOGIC CẬP NHẬT DỮ LIỆU (CRAWLER) ====================
  const btnUpdateJobs = document.getElementById("btnUpdateJobs");
  const updateStatusBanner = document.getElementById("updateStatusBanner");
  let pollInterval = null;

  if (btnUpdateJobs) {
    btnUpdateJobs.addEventListener("click", async () => {
      const originalText = btnUpdateJobs.textContent;
      btnUpdateJobs.disabled = true;
      btnUpdateJobs.textContent = "Đang cập nhật...";

      updateStatusBanner.className = "update-status-banner info";
      updateStatusBanner.textContent =
        "Hệ thống đang cào dữ liệu mới (Jobicy, Arbeitnow)... Vui lòng đợi.";
      updateStatusBanner.style.display = "block";

      try {
        const res = await fetch("/api/jobs/update", { method: "POST" });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Lỗi server");

        pollInterval = setInterval(async () => {
          const statusRes = await fetch("/api/jobs/update/status");
          const statusData = await statusRes.json();

          if (!statusData.is_running) {
            clearInterval(pollInterval);
            btnUpdateJobs.disabled = false;
            btnUpdateJobs.textContent = originalText;

            if (statusData.last_error) {
              updateStatusBanner.className = "update-status-banner error";
              updateStatusBanner.textContent = `Lỗi: ${statusData.last_error}`;
            } else {
              const d = statusData.last_result || {};
              updateStatusBanner.className = "update-status-banner success";
              updateStatusBanner.textContent = `Cập nhật thành công! Lưu ${d.saved_jobs || 0} job mới.`;
              setTimeout(
                () => (updateStatusBanner.style.display = "none"),
                5000,
              );
              loadJobs(currentPage);
            }
          }
        }, 2000);
      } catch (err) {
        btnUpdateJobs.disabled = false;
        btnUpdateJobs.textContent = originalText;
        updateStatusBanner.className = "update-status-banner error";
        updateStatusBanner.textContent = err.message;
      }
    });
  }
});
