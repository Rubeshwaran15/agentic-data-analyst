const API_BASE = "/api";

export async function uploadDatasetFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/datasets/upload`, {
    method: "POST",
    body: formData,
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || "Failed to upload dataset.");
  }
  return data;
}

export async function fetchDatasetPreview(datasetId) {
  const response = await fetch(`${API_BASE}/datasets/${datasetId}/preview`);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || "Failed to fetch dataset preview.");
  }
  return data;
}

export async function fetchDatasetProfile(datasetId) {
  const response = await fetch(`${API_BASE}/profiling/${datasetId}`);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || "Failed to fetch dataset profile.");
  }
  return data;
}

export async function fetchDatasetQuality(datasetId, targetColumn = "") {
  const query = targetColumn ? `?target_column=${encodeURIComponent(targetColumn)}` : "";
  const response = await fetch(`${API_BASE}/quality/${datasetId}${query}`);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || "Failed to fetch quality analysis.");
  }
  return data;
}

export async function fetchDatasetRecommendations(datasetId, targetColumn = "", userGoal = "") {
  const params = new URLSearchParams();
  if (targetColumn) params.set("target_column", targetColumn);
  if (userGoal) params.set("user_goal", userGoal);
  const qs = params.toString() ? `?${params.toString()}` : "";

  const response = await fetch(`${API_BASE}/recommendations/${datasetId}${qs}`);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || "Failed to fetch AI recommendations.");
  }
  return data;
}

export async function previewTransformation(datasetId, payload) {
  const response = await fetch(`${API_BASE}/transformations/${datasetId}/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || "Failed to preview transformation.");
  }
  return data;
}

export async function executeTransformation(datasetId, payload) {
  const response = await fetch(`${API_BASE}/transformations/${datasetId}/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...payload, approved_by_user: true }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || "Failed to execute transformation.");
  }
  return data;
}

export async function executeMLPipeline(datasetId, payload) {
  const response = await fetch(`${API_BASE}/transformations/${datasetId}/ml-pipeline`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...payload, approved_by_user: true }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || "Failed to execute ML pipeline.");
  }
  return data;
}

export async function fetchTransformationHistory(datasetId) {
  const response = await fetch(`${API_BASE}/transformations/${datasetId}/history`);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || "Failed to fetch transformation history.");
  }
  return data;
}

export async function undoLastTransformation(datasetId) {
  const response = await fetch(`${API_BASE}/transformations/${datasetId}/undo`, {
    method: "POST",
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || "Failed to undo transformation.");
  }
  return data;
}

export async function restoreDatasetVersion(datasetId, version) {
  const response = await fetch(
    `${API_BASE}/transformations/${datasetId}/restore/${version}`,
    { method: "POST" }
  );
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || "Failed to restore dataset version.");
  }
  return data;
}

export async function fetchBeforeAfterComparison(datasetId) {
  const response = await fetch(`${API_BASE}/transformations/${datasetId}/comparison`);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || "Failed to fetch before/after comparison.");
  }
  return data;
}

export function getCleanedDatasetDownloadUrl(datasetId, format = "csv") {
  return `${API_BASE}/exports/${datasetId}/dataset?format=${format}`;
}

export function getAuditReportDownloadUrl(datasetId, format = "html") {
  return `${API_BASE}/exports/${datasetId}/report?format=${format}`;
}

export function getSampleCsvDownloadUrl() {
  return `${API_BASE}/exports/sample-csv`;
}