export default function PrintButton() {
  return (
    <div className="area-print">
      <button onClick={() => window.print()} className="static-print-btn">
        🖨️ הדפס / שמור כ-PDF
      </button>
    </div>
  );
}
