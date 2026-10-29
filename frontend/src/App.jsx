import React, { useState } from "react";
import FileUpload from "./components/FileUpload";
import ColumnMappingReport from "./components/ColumnMappingReport";
import DatasetPreview from "./components/DatasetPreview";
import ProfileExplorer from "./components/ProfileExplorer";
import QualityDashboard from "./components/QualityDashboard";
import OutlierVisualizer from "./components/OutlierVisualizer";
import AIRecommendations from "./components/AIRecommendations";
import TransformationWorkbench from "./components/TransformationWorkbench";
import MLPipelineStudio from "./components/MLPipelineStudio";
import AuditHistoryAndCompare from "./components/AuditHistoryAndCompare";
import ExportCenter from "./components/ExportCenter";
import {
  uploadDatasetFile,
  fetchDatasetPreview,
  fetchDatasetProfile,
  fetchDatasetQuality,
  fetchDatasetRecommendations,
  fetchTransformationHistory,
  fetchBeforeAfterComparison,
} from "./services/api";

export default function App() {
  const [uploadData, setUploadData] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [profileData, setProfileData] = useState(null);
  const [qualityData, setQualityData] = useState(null);
  const [recommendationsData, setRecommendationsData] = useState(null);
  const [historyData, setHistoryData] = useState(null);
  const [comparisonData, setComparisonData] = useState(null);
  const [targetColumn, setTargetColumn] = useState("");
  const [userGoal, setUserGoal] = useState("");
  const [activeTab, setActiveTab] = useState("recommendations");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [statusBanner, setStatusBanner] = useState("");

  const refreshAllDatasetViews = async (
    datasetId,
    targetCol = targetColumn,
    goal = userGoal
  ) => {
    const [
      preview,
      profile,
      quality,
      recommendations,
      history,
      comparison,
    ] = await Promise.all([
      fetchDatasetPreview(datasetId),
      fetchDatasetProfile(datasetId),
      fetchDatasetQuality(datasetId, targetCol),
      fetchDatasetRecommendations(datasetId, targetCol, goal),
      fetchTransformationHistory(datasetId),
      fetchBeforeAfterComparison(datasetId),
    ]);
    setPreviewData(preview);
    setProfileData(profile);
    setQualityData(quality);
    setRecommendationsData(recommendations);
    setHistoryData(history);
    setComparisonData(comparison);
  };

  const handleFileUpload = async (file) => {
    setIsLoading(true);
    setErrorMsg("");
    setStatusBanner("");
    setTargetColumn("");
    try {
      const uploaded = await uploadDatasetFile(file);
      setUploadData(uploaded);
      setPreviewData(uploaded.preview);

      await refreshAllDatasetViews(uploaded.dataset_id, "", userGoal);
      setActiveTab("recommendations");
    } catch (err) {
      setErrorMsg(err.message || "Unexpected error during upload or analysis.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoalOrTargetUpdate = async (newTarget, newGoal, shouldFetch = true) => {
    setTargetColumn(newTarget);
    setUserGoal(newGoal);
    if (shouldFetch && uploadData?.dataset_id) {
      const [quality, recommendations] = await Promise.all([
        fetchDatasetQuality(uploadData.dataset_id, newTarget),
        fetchDatasetRecommendations(uploadData.dataset_id, newTarget, newGoal),
      ]);
      setQualityData(quality);
      setRecommendationsData(recommendations);
    }
  };

  const handleStateUpdated = async (message) => {
    if (!uploadData?.dataset_id) return;
    setStatusBanner(message);
    await refreshAllDatasetViews(uploadData.dataset_id, targetColumn, userGoal);
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>Agentic AI Data Preprocessing & Quality Analyst</h1>
          <p>
            Deterministic Python Profiling & Quality Engine + Local Ollama (Qwen2.5 1.5B)
          </p>
        </div>
        <span className="phase-badge">
          {historyData
            ? `Snapshot v${historyData.current_version} • Production Ready`
            : "Phase 7: Complete Agentic Suite"}
        </span>
      </header>

      {errorMsg && <div className="error-banner">{errorMsg}</div>}
      {statusBanner && <div className="success-banner">{statusBanner}</div>}

      <FileUpload onUploadSuccess={handleFileUpload} isLoading={isLoading} />

      {uploadData && profileData && qualityData && (
        <>
          <div className="kpi-grid">
            <div className="kpi-card">
              <div className="kpi-label">Dataset Dimensions</div>
              <div className="kpi-value">
                {profileData.row_count.toLocaleString()} × {profileData.column_count}
              </div>
              <div className="kpi-sub">
                {uploadData.filename} (v{historyData?.current_version ?? 0})
              </div>
            </div>

            <div className="kpi-card">
              <div className="kpi-label">Memory Usage</div>
              <div className="kpi-value">{profileData.memory_usage_human}</div>
              <div className="kpi-sub">
                {profileData.memory_usage_bytes.toLocaleString()} bytes in RAM
              </div>
            </div>

            <div className={`kpi-card ${qualityData.risk_score > 25 ? "kpi-alert" : ""}`}>
              <div className="kpi-label">Quality Risk Score</div>
              <div
                className="kpi-value"
                style={{
                  color: qualityData.risk_score > 25 ? "#BB232B" : "#20309A",
                }}
              >
                {qualityData.risk_score} / 100
              </div>
              <div className="kpi-sub">
                {qualityData.total_issues_found} issues ({qualityData.confirmed_issues_count} confirmed)
              </div>
            </div>

            <div className={`kpi-card ${profileData.total_missing_cells > 0 ? "kpi-alert" : ""}`}>
              <div className="kpi-label">Missing Values</div>
              <div
                className="kpi-value"
                style={{
                  color: profileData.total_missing_cells > 0 ? "#BB232B" : "#20309A",
                }}
              >
                {profileData.total_missing_cells.toLocaleString()}
              </div>
              <div className="kpi-sub">
                {profileData.total_missing_percentage}% of all cells
              </div>
            </div>

            <div className="kpi-card">
              <div className="kpi-label">Audit Steps Executed</div>
              <div className="kpi-value">{historyData?.current_version ?? 0}</div>
              <div className="kpi-sub">
                {historyData?.can_undo ? "Undo & Export Ready" : "At baseline v0"}
              </div>
            </div>
          </div>

          <div className="tabs-bar">
            <button
              className={`tab-btn ${activeTab === "recommendations" ? "active" : ""}`}
              onClick={() => setActiveTab("recommendations")}
            >
              AI Recommendations ({recommendationsData?.recommendations?.length || 0})
            </button>
            <button
              className={`tab-btn ${activeTab === "workbench" ? "active" : ""}`}
              onClick={() => setActiveTab("workbench")}
            >
              Workbench
            </button>
            <button
              className={`tab-btn ${activeTab === "ml" ? "active" : ""}`}
              onClick={() => setActiveTab("ml")}
            >
              ML-Ready Pipeline Studio
            </button>
            <button
              className={`tab-btn ${activeTab === "outliers" ? "active" : ""}`}
              onClick={() => setActiveTab("outliers")}
            >
              Outlier Visualizer ({qualityData.outlier_summaries?.length || 0})
            </button>
            <button
              className={`tab-btn ${activeTab === "quality" ? "active" : ""}`}
              onClick={() => setActiveTab("quality")}
            >
              Quality Checks ({qualityData.total_issues_found})
            </button>
            <button
              className={`tab-btn ${activeTab === "history" ? "active" : ""}`}
              onClick={() => setActiveTab("history")}
            >
              Validation & Undo ({historyData?.entries?.length || 1})
            </button>
            <button
              className={`tab-btn ${activeTab === "exports" ? "active" : ""}`}
              onClick={() => setActiveTab("exports")}
            >
              Exports & Audit Reports
            </button>
            <button
              className={`tab-btn ${activeTab === "profile" ? "active" : ""}`}
              onClick={() => setActiveTab("profile")}
            >
              Column Profiles
            </button>
            <button
              className={`tab-btn ${activeTab === "mapping" ? "active" : ""}`}
              onClick={() => setActiveTab("mapping")}
            >
              Header Mapping
            </button>
            <button
              className={`tab-btn ${activeTab === "preview" ? "active" : ""}`}
              onClick={() => setActiveTab("preview")}
            >
              10-Row Preview
            </button>
          </div>

          {activeTab === "recommendations" && (
            <AIRecommendations
              datasetId={uploadData.dataset_id}
              columns={previewData?.columns || []}
              targetColumn={targetColumn}
              userGoal={userGoal}
              onGoalOrTargetUpdate={handleGoalOrTargetUpdate}
              recommendations={recommendationsData}
              onTransformationApplied={handleStateUpdated}
            />
          )}
          {activeTab === "workbench" && (
            <TransformationWorkbench
              datasetId={uploadData.dataset_id}
              columns={previewData?.columns || []}
              onTransformationApplied={handleStateUpdated}
            />
          )}
          {activeTab === "ml" && (
            <MLPipelineStudio
              datasetId={uploadData.dataset_id}
              columns={previewData?.columns || []}
              targetColumn={targetColumn}
              onTargetColumnChange={(col) => handleGoalOrTargetUpdate(col, userGoal, true)}
              onPipelineCompleted={handleStateUpdated}
            />
          )}
          {activeTab === "outliers" && (
            <OutlierVisualizer
              datasetId={uploadData.dataset_id}
              outlierSummaries={qualityData.outlier_summaries}
              onTransformationApplied={handleStateUpdated}
            />
          )}
          {activeTab === "quality" && <QualityDashboard quality={qualityData} />}
          {activeTab === "history" && (
            <AuditHistoryAndCompare
              datasetId={uploadData.dataset_id}
              historyData={historyData}
              comparisonData={comparisonData}
              onStateRestored={handleStateUpdated}
            />
          )}
          {activeTab === "exports" && (
            <ExportCenter
              datasetId={uploadData.dataset_id}
              filename={uploadData.filename}
              comparisonData={comparisonData}
              historyData={historyData}
            />
          )}
          {activeTab === "profile" && <ProfileExplorer profile={profileData} />}
          {activeTab === "mapping" && (
            <ColumnMappingReport report={uploadData.standardization_report} />
          )}
          {activeTab === "preview" && <DatasetPreview preview={previewData} />}
        </>
      )}
    </div>
  );
}