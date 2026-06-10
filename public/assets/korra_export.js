/**
 * KORRA Export Engine | Block 5: Portability
 * =========================================
 * Industrial-grade PDF and CSV generation for digital biometrics.
 * Formatted for Master Artisan Workshop floors.
 */

window.KORRA_EXPORT = {

    pdf: async function(clientName, measurements, gender, height) {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();

        // 1. Branding & Header (Obsidian & Mint Style)
        doc.setFillColor(0, 0, 0); // Obsidian
        doc.rect(0, 0, 210, 40, 'F');

        doc.setTextColor(87, 215, 192); // Mint
        doc.setFontSize(28);
        doc.setFont("helvetica", "bold");
        doc.text("KORRA AI", 20, 25);

        doc.setTextColor(255, 255, 255);
        doc.setFontSize(10);
        doc.text("DIGITAL ARTISAN INFRASTRUCTURE", 20, 32);

        // 2. Client Profile
        doc.setTextColor(0, 0, 0);
        doc.setFontSize(16);
        doc.text("Technical Measurement Sheet", 20, 55);

        doc.setFontSize(10);
        doc.setTextColor(100, 100, 100);
        doc.text(`CLIENT: ${clientName.toUpperCase()}`, 20, 65);
        doc.text(`GENDER: ${gender.toUpperCase()}  |  HEIGHT: ${height}cm`, 20, 70);
        doc.text(`DATE: ${new Date().toLocaleDateString()}`, 20, 75);

        // 3. Measurement Grid
        let y = 90;
        doc.setDrawColor(230, 230, 230);
        doc.line(20, y - 5, 190, y - 5);

        doc.setFontSize(12);
        doc.setTextColor(0, 0, 0);

        const keys = Object.keys(measurements);
        keys.forEach((key, index) => {
            const val = measurements[key];
            doc.text(`${key}:`, 25, y);
            doc.setFont("helvetica", "bold");
            doc.text(`${val} cm`, 100, y);
            doc.setFont("helvetica", "normal");

            doc.line(20, y + 3, 190, y + 3);
            y += 10;

            // Handle page overflow if many measurements
            if (y > 270) {
                doc.addPage();
                y = 20;
            }
        });

        // 4. Footer
        doc.setFontSize(8);
        doc.setTextColor(150, 150, 150);
        doc.text("VERIFIED BY KORRA VOLUMETRIC ENGINE V2.1.2 | London • Lagos", 20, 285);

        doc.save(`KORRA_MEASUREMENTS_${clientName.replace(/\s+/g, '_')}.pdf`);
    },

    csv: function(dataArray) {
        // Implementation for batch CSV export
        let csvContent = "data:text/csv;charset=utf-8,";
        csvContent += "Client,Gender,Height,Chest,Waist,Hips,Shoulder,Inseam\n";

        dataArray.forEach(row => {
            const m = row.measurements;
            csvContent += `${row.client_name},${row.gender},${row.height},${m['Chest Round']},${m['Waist Round']},${m['Hip Round']},${m['Shoulder']},${m['Inseam']}\n`;
        });

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "KORRA_BATCH_EXPORT.csv");
        document.body.appendChild(link);
        link.click();
    },

    obj: function(meshUrl, clientName) {
        if (!meshUrl) {
            alert("No physical 3D twin found for this scan.");
            return;
        }
        const link = document.createElement("a");
        link.href = meshUrl;
        link.download = `KORRA_MESH_${clientName.replace(/\s+/g, '_')}.obj`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
};
