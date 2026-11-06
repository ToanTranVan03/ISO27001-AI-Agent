
const sleep = (ms) =>
  new Promise((resolve) => setTimeout(resolve, ms));

const RUNNING = new Set([
  "queued", "pending", "running", "processing",
  "in_progress", "started",
]);

const FINISHED = new Set([
  "completed", "complete", "done",
  "success", "succeeded", "finished",
]);

const FAILED = new Set([
  "failed", "error", "cancelled", "canceled",
]);

const WAITING = new Set([
  "waiting_evidence", "needs_evidence",
  "waiting_for_evidence", "waiting_input",
  "needs_input",
]);

function getStatus(data) {
  return String(
    data?.status ??
    data?.job?.status ??
    data?.state ??
    ""
  ).toLowerCase();
}

function needsEvidence(data) {
  const output = data?.result ?? data?.output ?? {};
  const status = String(
    output?.status ??
    output?.iso_status ??
    output?.assessment_status ??
    ""
  ).toLowerCase();

  return (
    data?.needs_evidence === true ||
    output?.needs_evidence === true ||
    (Array.isArray(output?.missing_evidence) &&
      output.missing_evidence.length > 0) ||
    WAITING.has(status)
  );
}

export async function runA61Pilot({
  request,
  assessmentId,
  onEvent = () => {},
}) {
  if (!assessmentId || typeof request !== "function") {
    throw new Error("Thiếu assessmentId hoặc API request.");
  }

  const controlId = "A.6.1";
  const base = `/api/assessments/${encodeURIComponent(
    assessmentId
  )}/controls/${controlId}`;

  onEvent({
    type: "action",
    text: `Khởi tạo Agent thật cho ${controlId}.`,
  });

  // API đã xác nhận có POST /run và không yêu cầu JSON body.
  const started = await request(`${base}/run`, {
    method: "POST",
  });

  const jobId =
    started?.job_id ??
    started?.job?.job_id ??
    started?.job?.id ??
    started?.id;

  if (!jobId) {
    throw new Error(
      "API /run không trả job_id ở cấu trúc đã nhận biết. " +
      "Các trường nhận được: " +
      Object.keys(started ?? {}).join(", ")
    );
  }

  onEvent({
    type: "execute",
    text: `Backend đã tạo job ${jobId}.`,
  });

  let previousStatus = "";

  // Theo dõi tối đa 90 lần, mỗi lần cách nhau 2 giây.
  for (let attempt = 0; attempt < 90; attempt++) {
    const job = await request(
      `/api/jobs/${encodeURIComponent(jobId)}`
    );

    const status = getStatus(job);

    if (status !== previousStatus) {
      onEvent({
        type: "execute",
        text: `Job ${jobId}: ${status || "không rõ trạng thái"}`,
      });
      previousStatus = status;
    }

    if (WAITING.has(status) || needsEvidence(job)) {
      onEvent({
        type: "warning",
        text: `${controlId} cần bổ sung bằng chứng hoặc dữ liệu.`,
      });

      return {
        outcome: "waiting",
        jobId,
        job,
        controlId,
      };
    }

    if (FAILED.has(status)) {
      throw new Error(
        `Job ${jobId} thất bại: ${
          job.error ?? job.message ?? status
        }`
      );
    }

    if (FINISHED.has(status)) {
      onEvent({
        type: "success",
        text:
          `Job ${jobId} đã kết thúc xử lý. ` +
          "Cần đọc kết quả ISO trước khi kết luận tuân thủ.",
      });

      return {
        outcome: "finished",
        jobId,
        job,
        controlId,
      };
    }

    if (!RUNNING.has(status)) {
      throw new Error(
        `Trạng thái job chưa được hỗ trợ: ${status || "(trống)"}`
      );
    }

    await sleep(2000);
  }

  throw new Error(
    `Job ${jobId} vượt thời gian theo dõi 180 giây. ` +
    "Job có thể vẫn đang chạy trong backend."
  );
}
