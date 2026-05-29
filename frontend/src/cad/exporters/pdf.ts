/**
 * Triggers standard browser print dialog for stylesheet-optimized PDF report exports.
 */
export function exportPdf() {
  if (typeof window !== "undefined") {
    window.print();
  }
}
