document.addEventListener('DOMContentLoaded', function() {
    // Alle Tabellen mit der Klasse 'sortable' sortierbar machen
    const tables = document.querySelectorAll('.data-table');
    
    tables.forEach(table => {
        makeSortable(table);
    });
});

function makeSortable(table) {
    const headers = table.querySelectorAll('th');
    
    headers.forEach((header, index) => {
        // Skip Aktionen-Spalte
        if (header.textContent.trim() === 'Aktionen') return;
        
        header.style.cursor = 'pointer';
        header.style.userSelect = 'none';
        header.classList.add('sortable-header');
        
        // Sort-Indikator hinzufügen
        const sortIndicator = document.createElement('span');
        sortIndicator.className = 'sort-indicator';
        sortIndicator.innerHTML = '↕️';
        header.appendChild(sortIndicator);
        
        header.addEventListener('click', () => {
            sortTable(table, index, header);
        });
    });
}

function sortTable(table, columnIndex, header) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Aktuelle Sortierrichtung bestimmen
    const isAscending = header.classList.contains('sort-asc');
    const isDescending = header.classList.contains('sort-desc');
    
    // Alle anderen Headers zurücksetzen
    table.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
        const indicator = th.querySelector('.sort-indicator');
        if (indicator) indicator.innerHTML = '↕️';
    });
    
    // Sortierrichtung festlegen
    let sortAscending = true;
    if (!isAscending && !isDescending) {
        sortAscending = true; // Erste Klick: aufsteigend
    } else if (isAscending) {
        sortAscending = false; // Zweite Klick: absteigend
    } else {
        sortAscending = true; // Dritte Klick: wieder aufsteigend
    }
    
    // Rows sortieren
    rows.sort((a, b) => {
        const aText = a.cells[columnIndex].textContent.trim();
        const bText = b.cells[columnIndex].textContent.trim();
        
        // Versuche als Zahl zu sortieren
        const aNum = parseFloat(aText);
        const bNum = parseFloat(bText);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return sortAscending ? aNum - bNum : bNum - aNum;
        }
        
        // Datum-Sortierung (falls Format erkannt wird)
        const aDate = new Date(aText);
        const bDate = new Date(bText);
        
        if (!isNaN(aDate.getTime()) && !isNaN(bDate.getTime())) {
            return sortAscending ? aDate - bDate : bDate - aDate;
        }
        
        // Text-Sortierung
        const comparison = aText.localeCompare(bText, 'de', { numeric: true });
        return sortAscending ? comparison : -comparison;
    });
    
    // Sortierte Rows wieder einfügen
    rows.forEach(row => tbody.appendChild(row));
    
    // Header-Klassen und Indikator aktualisieren
    if (sortAscending) {
        header.classList.add('sort-asc');
        header.querySelector('.sort-indicator').innerHTML = '↑';
    } else {
        header.classList.add('sort-desc');
        header.querySelector('.sort-indicator').innerHTML = '↓';
    }
}

// Mobile Tabellen-Verbesserung
function initMobileTables() {
    const tables = document.querySelectorAll('.data-table');
    
    tables.forEach(table => {
        // Wrapper für horizontales Scrollen auf Mobile
        if (!table.parentElement.classList.contains('table-wrapper')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'table-wrapper';
            table.parentElement.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }
    });
}

// Bei Seitenload Mobile-Optimierungen anwenden
document.addEventListener('DOMContentLoaded', initMobileTables);