import React, { useState, useEffect, useMemo } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell, LabelList,
} from "recharts";
import { Fuel, Plus, Upload, Trash2, Droplet, Sunrise, Sun, Moon, Download, ChevronDown, ChevronRight, ShoppingBag, TrendingUp } from "lucide-react";
import Papa from "papaparse";
import * as XLSX from "xlsx";

const THEME = {
  bg: "#0E1B2A",
  surface: "#152840",
  surfaceLight: "#1C3352",
  border: "#2A4361",
  ink: "#F4EFE6",
  inkDim: "#9FB1C6",
  amber: "#4FA3E0",
  amberDim: "#16324D",
  naftaSuper: "#E4572E",
  naftaPremium: "#F2C14E",
  diesel: "#2E9E6B",
  dieselPremium: "#3FA7D6",
};

const YEAR_COLORS = { 2025: "#3FA7D6", 2026: "#4C5FAE" };

const PRODUCTOS = ["Nafta Súper", "Infinia", "Diesel 500", "Infinia Diesel"];
const PRODUCT_COLOR = {
  "Nafta Súper": THEME.naftaSuper,
  "Infinia": THEME.naftaPremium,
  "Diesel 500": THEME.diesel,
  "Infinia Diesel": THEME.dieselPremium,
};
const NAFTAS = ["Nafta Súper", "Infinia"];
const DIESELS = ["Diesel 500", "Infinia Diesel"];
const TURNOS = ["Mañana", "Tarde", "Noche"];
const TURNOS_TIENDA = ["Mañana", "Tarde"];
const TURNO_ICON = { "Mañana": Sunrise, "Tarde": Sun, "Noche": Moon };
const MESES = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"];
const YEARS = [2025, 2026];
const STORAGE_KEY = "ventas-estacion-entries";
const STORAGE_KEY_TIENDA = "tienda-full-entries";

// Reconoce la planilla cruda del aforador (columnas NAFTA SUPER, DIESEL 500, INFINIA NAFTA,
// INFINIA DIESEL) y filas tipo "Tue 01/07/2025 (1)" con el turno como sufijo.
const RAW_PRODUCT_MAP = {
  "NAFTA SUPER": "Nafta Súper",
  "DIESEL 500": "Diesel 500",
  "INFINIA NAFTA": "Infinia",
  "INFINIA DIESEL": "Infinia Diesel",
};
const RAW_TURNO_MAP = { "1": "Noche", "2": "Mañana", "3": "Tarde" };
const RAW_DATE_RE = /(\d{2})\/(\d{2})\/(\d{4})\s*\((\d)\)/;

function entryKey(e) { return `${e.fecha}|${e.turno}|${e.producto}`; }
function tiendaEntryKey(e) { return `${e.fecha}|${e.turno}|${e.categoria}`; }

function normalizeTiendaTurno(raw) {
  const s = String(raw || "").trim().toLowerCase().replace(/[.\s]/g, "");
  if (s === "tm" || s.startsWith("mañ") || s.startsWith("man")) return "Mañana";
  if (s === "tt" || s.startsWith("tar")) return "Tarde";
  return null;
}

function uid() { return Math.random().toString(36).slice(2, 10); }

function fmtNum(n) {
  return new Intl.NumberFormat("es-AR", { maximumFractionDigits: 0, useGrouping: false }).format(n || 0);
}
function fmtGrouped(n) {
  return new Intl.NumberFormat("es-AR", { maximumFractionDigits: 0, useGrouping: true }).format(Math.round(n || 0));
}
function fmtMoney(n) {
  return new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0, useGrouping: false }).format(n || 0);
}

function PumpNumber({ value, label, color, prefix }) {
  const digits = fmtNum(value).split("");
  return (
    <div>
      <div style={{ display: "flex", gap: 3 }}>
        {prefix && (
          <div style={{
            fontFamily: "'JetBrains Mono', monospace", fontSize: 22, color: THEME.inkDim,
            alignSelf: "flex-end", marginRight: 2, marginBottom: 4,
          }}>{prefix}</div>
        )}
        {digits.map((d, i) => (
          <div key={i} style={{
            background: "#081220",
            border: `1px solid ${THEME.border}`,
            borderRadius: 3,
            width: d === "." || d === "," ? 10 : 24,
            height: 38,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 22, fontWeight: 700,
            color: color || THEME.amber,
            textShadow: `0 0 10px ${(color || THEME.amber)}55`,
            boxShadow: "inset 0 2px 4px rgba(0,0,0,0.5)",
          }}>{d}</div>
        ))}
      </div>
      <div style={{ fontFamily: "'Oswald', sans-serif", fontSize: 11, letterSpacing: 1.5, textTransform: "uppercase", color: THEME.inkDim, marginTop: 6 }}>
        {label}
      </div>
    </div>
  );
}

function Card({ children, style }) {
  return (
    <div style={{
      background: THEME.surface, border: `1px solid ${THEME.border}`,
      borderRadius: 10, padding: 20, ...style,
    }}>{children}</div>
  );
}

function SectionTitle({ children, icon: Icon }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
      {Icon && <Icon size={16} color={THEME.amber} />}
      <h3 style={{
        fontFamily: "'Oswald', sans-serif", fontSize: 15, letterSpacing: 1,
        textTransform: "uppercase", color: THEME.ink, margin: 0, fontWeight: 600,
      }}>{children}</h3>
    </div>
  );
}

export default function App() {
  const [section, setSection] = useState("combustible");
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("cargar");
  const [form, setForm] = useState({
    fecha: new Date().toISOString().slice(0, 10),
    turno: "Mañana", producto: "Nafta Súper", litros: "", importe: "", 
  });
  const [importMsg, setImportMsg] = useState(null);
  const [selectedMonth, setSelectedMonth] = useState(null);
  const [showClearModal, setShowClearModal] = useState(false);
  const [clearPassword, setClearPassword] = useState("");
  const [clearError, setClearError] = useState(null);
  const [clearTargetIds, setClearTargetIds] = useState([]);
  const [clearScopeLabel, setClearScopeLabel] = useState("");
  const [clearKind, setClearKind] = useState("combustible");
  const [filterYear, setFilterYear] = useState("todos");
  const [filterMonth, setFilterMonth] = useState(null);
  const [expandedDates, setExpandedDates] = useState(new Set());
  const [showManualForm, setShowManualForm] = useState(false);

  // ---- Tienda Full ----
  const [tiendaEntries, setTiendaEntries] = useState([]);
  const [tiendaLoading, setTiendaLoading] = useState(true);
  const [tiendaForm, setTiendaForm] = useState({
    fecha: new Date().toISOString().slice(0, 10),
    turno: "Mañana", categoria: "", importe: "",
  });
  const [tiendaImportMsg, setTiendaImportMsg] = useState(null);
  const [tiendaSelectedMonth, setTiendaSelectedMonth] = useState(null);
  const [tiendaFilterYear, setTiendaFilterYear] = useState("todos");
  const [tiendaFilterMonth, setTiendaFilterMonth] = useState(null);
  const [tiendaExpandedDates, setTiendaExpandedDates] = useState(new Set());
  const [tiendaShowManualForm, setTiendaShowManualForm] = useState(false);

  useEffect(() => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap";
    document.head.appendChild(link);
    return () => document.head.removeChild(link);
  }, []);

  useEffect(() => {
    (async () => {
      try {
        let res = await window.storage.get(STORAGE_KEY, true);
        if (!res || !res.value) {
          // Migración única: si había datos guardados como personales (antes de compartir), los copia al storage compartido.
          try {
            const personal = await window.storage.get(STORAGE_KEY, false);
            if (personal && personal.value) {
              await window.storage.set(STORAGE_KEY, personal.value, true);
              res = personal;
            }
          } catch (eMig) { /* sin datos personales previos */ }
        }
        if (res && res.value) setEntries(JSON.parse(res.value));
      } catch (e) { /* no data yet */ }
      setLoading(false);
    })();
  }, []);

  useEffect(() => {
    (async () => {
      try {
        let res = await window.storage.get(STORAGE_KEY_TIENDA, true);
        if (!res || !res.value) {
          try {
            const personal = await window.storage.get(STORAGE_KEY_TIENDA, false);
            if (personal && personal.value) {
              await window.storage.set(STORAGE_KEY_TIENDA, personal.value, true);
              res = personal;
            }
          } catch (eMig) { /* sin datos personales previos */ }
        }
        if (res && res.value) setTiendaEntries(JSON.parse(res.value));
      } catch (e) { /* no data yet */ }
      setTiendaLoading(false);
    })();
  }, []);

  async function persist(next) {
    setEntries(next);
    try {
      await window.storage.set(STORAGE_KEY, JSON.stringify(next), true);
    } catch (e) {
      console.error("No se pudo guardar", e);
    }
  }

  async function persistTienda(next) {
    setTiendaEntries(next);
    try {
      await window.storage.set(STORAGE_KEY_TIENDA, JSON.stringify(next), true);
    } catch (e) {
      console.error("No se pudo guardar", e);
    }
  }

  function addEntry(e) {
    e.preventDefault();
    if (!form.fecha || !form.litros) return;
    const next = [...entries, {
      id: uid(), fecha: form.fecha, turno: form.turno, producto: form.producto,
      litros: parseFloat(form.litros) || 0, importe: parseFloat(form.importe) || 0,
    }];
    persist(next);
    setForm({ ...form, litros: "", importe: "" });
  }

  function addTiendaEntry(e) {
    e.preventDefault();
    if (!tiendaForm.fecha || !tiendaForm.categoria || !tiendaForm.importe) return;
    const next = [...tiendaEntries, {
      id: uid(), fecha: tiendaForm.fecha, turno: tiendaForm.turno, categoria: tiendaForm.categoria.trim(),
      importe: parseFloat(tiendaForm.importe) || 0, cantidad: 0,
    }];
    persistTienda(next);
    setTiendaForm({ ...tiendaForm, categoria: "", importe: "" });
  }

  function removeEntry(id) {
    persist(entries.filter((x) => x.id !== id));
  }

  function openClearModal(kind, ids, label) {
    setClearKind(kind);
    setClearTargetIds(ids);
    setClearScopeLabel(label);
    setClearPassword("");
    setClearError(null);
    setShowClearModal(true);
  }

  function clearAll() {
    openClearModal("combustible", entries.map((e) => e.id), `todos los registros (${entries.length})`);
  }

  function clearFiltered() {
    const ids = filteredEntries.map((e) => e.id);
    const label = `los registros de ${filterMonth === null ? "" : MESES[filterMonth] + " "}${filterYear === "todos" ? "(todos los años)" : filterYear} (${ids.length})`;
    openClearModal("combustible", ids, label);
  }

  function clearAllTienda() {
    openClearModal("tienda", tiendaEntries.map((e) => e.id), `todos los registros de tienda (${tiendaEntries.length})`);
  }

  function clearFilteredTienda() {
    const ids = filteredTiendaEntries.map((e) => e.id);
    const label = `los registros de tienda de ${tiendaFilterMonth === null ? "" : MESES[tiendaFilterMonth] + " "}${tiendaFilterYear === "todos" ? "(todos los años)" : tiendaFilterYear} (${ids.length})`;
    openClearModal("tienda", ids, label);
  }

  function confirmClearAll() {
    if (clearPassword !== "Ingreso01") {
      setClearError("Clave incorrecta.");
      return;
    }
    const idsToRemove = new Set(clearTargetIds);
    if (clearKind === "tienda") {
      persistTienda(tiendaEntries.filter((x) => !idsToRemove.has(x.id)));
      setTiendaImportMsg(null);
    } else {
      persist(entries.filter((x) => !idsToRemove.has(x.id)));
      setImportMsg(null);
    }
    setShowClearModal(false);
  }

  function finishImport(parsed, errors, sourceLabel) {
    const existingKeys = new Set(entries.map(entryKey));
    const seen = new Set();
    const fresh = [];
    let duplicates = 0;
    parsed.forEach((row) => {
      const k = entryKey(row);
      if (existingKeys.has(k) || seen.has(k)) { duplicates++; return; }
      seen.add(k);
      fresh.push(row);
    });
    if (fresh.length) persist([...entries, ...fresh]);
    const parts = [`${fresh.length} registros nuevos agregados`];
    if (duplicates) parts.push(`${duplicates} ya estaban cargados y se omitieron`);
    if (errors) parts.push(`${errors} filas con datos inválidos`);
    setImportMsg(`${sourceLabel}: ${parts.join(" · ")}.`);
  }

  function handleCSV(file) {
    Papa.parse(file, {
      header: true, skipEmptyLines: true,
      complete: (results) => {
        const parsed = [];
        let errors = 0;
        results.data.forEach((r) => {
          const fecha = (r.fecha || r.Fecha || "").trim();
          const turno = (r.turno || r.Turno || "").trim();
          const producto = (r.producto || r.Producto || "").trim();
          const litros = parseFloat(r.litros || r.Litros);
          const importe = parseFloat(r.importe || r.Importe) || 0;
          const turnoOk = TURNOS.find((t) => t.toLowerCase() === turno.toLowerCase());
          const productoOk = PRODUCTOS.find((p) => p.toLowerCase() === producto.toLowerCase());
          if (!fecha || !turnoOk || !productoOk || isNaN(litros)) { errors++; return; }
          parsed.push({ id: uid(), fecha, turno: turnoOk, producto: productoOk, litros, importe });
        });
        finishImport(parsed, errors, "CSV");
      },
      error: () => setImportMsg("No se pudo leer el archivo. Verificá que sea un CSV válido."),
    });
  }

  function handleRawXlsx(file) {
    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const wb = XLSX.read(evt.target.result, { type: "array" });
        const sheet = wb.Sheets[wb.SheetNames[0]];
        const rows = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: null });
        // Buscar la fila de encabezados reales (contiene "Fecha Apertura")
        let headerIdx = rows.findIndex((r) => r.some((c) => String(c || "").toLowerCase().includes("fecha apertura")));
        if (headerIdx === -1) { setImportMsg("No reconocí el formato de esta planilla."); return; }
        const headers = rows[headerIdx].map((c) => String(c || "").trim().toUpperCase());
        const colIdx = {};
        Object.keys(RAW_PRODUCT_MAP).forEach((key) => {
          const idx = headers.findIndex((h) => h === key);
          if (idx !== -1) colIdx[key] = idx;
        });
        const parsed = [];
        let errors = 0;
        for (let i = headerIdx + 1; i < rows.length; i++) {
          const row = rows[i];
          if (!row || row.every((c) => c === null || c === "")) continue;
          const cell = row[0];
          const m = RAW_DATE_RE.exec(String(cell || ""));
          if (!m) { errors++; continue; }
          const [, dd, mm, yyyy, turnoN] = m;
          const fecha = `${yyyy}-${mm}-${dd}`;
          const turno = RAW_TURNO_MAP[turnoN] || "Mañana";
          Object.entries(RAW_PRODUCT_MAP).forEach(([rawCol, producto]) => {
            const idx = colIdx[rawCol];
            if (idx === undefined) return;
            const val = parseFloat(row[idx]);
            if (!val || isNaN(val)) return;
            parsed.push({ id: uid(), fecha, turno, producto, litros: val, importe: 0 });
          });
        }
        finishImport(parsed, errors, "Planilla");
      } catch (e) {
        setImportMsg("No se pudo leer el archivo. Verificá que sea la planilla del aforador (.xlsx).");
      }
    };
    reader.readAsArrayBuffer(file);
  }

  function handleFile(file) {
    const name = file.name.toLowerCase();
    if (name.endsWith(".csv")) handleCSV(file);
    else if (name.endsWith(".xlsx") || name.endsWith(".xls")) handleRawXlsx(file);
    else setImportMsg("Formato no reconocido. Subí un .csv o la planilla .xlsx del aforador.");
  }

  function downloadTemplate() {
    const csv = "fecha,turno,producto,litros,importe\n2026-08-01,Mañana,Nafta Súper,320,480000\n2026-08-01,Tarde,Diesel 500,510,690000\n";
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "plantilla_ventas.csv"; a.click();
    URL.revokeObjectURL(url);
  }

  function finishTiendaImport(parsed, errors, sourceLabel) {
    const existingKeys = new Set(tiendaEntries.map(tiendaEntryKey));
    const seen = new Set();
    const fresh = [];
    let duplicates = 0;
    parsed.forEach((row) => {
      const k = tiendaEntryKey(row);
      if (existingKeys.has(k) || seen.has(k)) { duplicates++; return; }
      seen.add(k);
      fresh.push(row);
    });
    if (fresh.length) persistTienda([...tiendaEntries, ...fresh]);
    const parts = [`${fresh.length} registros nuevos agregados`];
    if (duplicates) parts.push(`${duplicates} ya estaban cargados y se omitieron`);
    if (errors) parts.push(`${errors} filas con datos inválidos`);
    setTiendaImportMsg(`${sourceLabel}: ${parts.join(" · ")}.`);
  }

  function handleTiendaCSV(file) {
    Papa.parse(file, {
      header: true, skipEmptyLines: true,
      complete: (results) => {
        const parsed = [];
        let errors = 0;
        results.data.forEach((r) => {
          const fecha = (r.fecha || r.Fecha || "").trim();
          const turno = (r.turno || r.Turno || "").trim();
          const categoria = (r.categoria || r.Categoria || r.producto || r.Producto || "").trim();
          const importe = parseFloat(r.importe || r.Importe);
          const cantidad = parseFloat(r.cantidad || r.Cantidad);
          const turnoOk = normalizeTiendaTurno(turno);
          if (!fecha || !turnoOk || !categoria || isNaN(importe)) { errors++; return; }
          parsed.push({ id: uid(), fecha, turno: turnoOk, categoria, importe, cantidad: isNaN(cantidad) ? 0 : cantidad });
        });
        finishTiendaImport(parsed, errors, "CSV");
      },
      error: () => setTiendaImportMsg("No se pudo leer el archivo. Verificá que sea un CSV válido."),
    });
  }

  function handleTiendaHtm(file) {
    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const raw = evt.target.result;
        const lines = [...raw.matchAll(/<FONT[^>]*>([^<]*)<\/FONT>/gi)].map((m) => m[1].trim());
        const fullText = lines.join("\n");

        // Turno: sale del nombre del archivo ("...TM.htm" / "...TT.htm")
        const base = file.name.replace(/\.[^.]+$/, "").toUpperCase();
        let turno = null;
        if (/(^|[^A-Z])TM$/.test(base)) turno = "Mañana";
        else if (/(^|[^A-Z])TT$/.test(base)) turno = "Tarde";
        if (!turno) {
          setTiendaImportMsg(`${file.name}: no pude reconocer el turno por el nombre del archivo (debe terminar en TM o TT).`);
          return;
        }

        // Fecha: la busca dentro del reporte (rendiciones parciales), formato dd/mm/aaaa
        const dateMatch = fullText.match(/(\d{2})\/(\d{2})\/(\d{4})/);
        if (!dateMatch) {
          setTiendaImportMsg(`${file.name}: no encontré una fecha dentro del reporte.`);
          return;
        }
        const [, dd, mm, yyyy] = dateMatch;
        const fecha = `${yyyy}-${mm}-${dd}`;

        // Rubros: líneas tipo "02-198 Comidas Envasad    4,0    54300,00"
        const rubroRe = /^(\d{2}-\d{3})\s+(\S.*?)\s{2,}(-?[\d.]+,\d+)\s+(-?[\d.]+,\d+)\s*$/;
        const parsed = [];
        let errors = 0;
        lines.forEach((line) => {
          const m = rubroRe.exec(line);
          if (!m) return;
          const categoria = m[2].trim();
          const cantidad = parseInt(m[3].split(",")[0].replace(/\./g, ""), 10);
          const importe = parseFloat(m[4].replace(/\./g, "").replace(",", "."));
          if (isNaN(importe)) { errors++; return; }
          parsed.push({ id: uid(), fecha, turno, categoria, importe, cantidad: isNaN(cantidad) ? 0 : cantidad });
        });

        if (!parsed.length) {
          setTiendaImportMsg(`${file.name}: no encontré rubros para importar. Revisá que sea un reporte "Cierre de Caja".`);
          return;
        }
        finishTiendaImport(parsed, errors, `Reporte ${fecha} (${turno})`);
      } catch (e) {
        setTiendaImportMsg(`${file.name}: no se pudo leer el archivo.`);
      }
    };
    reader.readAsText(file, "windows-1252");
  }

  function handleTiendaFile(file) {
    const name = file.name.toLowerCase();
    if (name.endsWith(".csv")) handleTiendaCSV(file);
    else if (name.endsWith(".htm") || name.endsWith(".html")) handleTiendaHtm(file);
    else setTiendaImportMsg("Formato no reconocido. Subí el reporte .htm de cierre de caja, o un CSV.");
  }

  function downloadTiendaTemplate() {
    const csv = "fecha,turno,categoria,importe\n2026-08-01,Mañana,Kiosco,45000\n2026-08-01,Tarde,Café/Bar,32000\n";
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "plantilla_tienda.csv"; a.click();
    URL.revokeObjectURL(url);
  }

  // ---- aggregations ----
  const withYear = useMemo(() => entries.map((e) => ({
    ...e, year: parseInt(String(e.fecha).slice(0, 4), 10),
    month: new Date(e.fecha + "T00:00:00").getMonth(),
  })), [entries]);

  const monthProjection = useMemo(() => {
    if (!withYear.length) return null;
    let y, m;
    if (selectedMonth !== null) {
      m = selectedMonth;
      const yearsWithMonth = withYear.filter((e) => e.month === m).map((e) => e.year);
      y = yearsWithMonth.length ? Math.max(...yearsWithMonth) : Math.max(...withYear.map((e) => e.year));
    } else {
      const latest = withYear.reduce((max, e) => (e.fecha > max.fecha ? e : max), withYear[0]);
      y = latest.year; m = latest.month;
    }
    const monthEntries = withYear.filter((e) => e.year === y && e.month === m);
    const daysWithData = new Set(monthEntries.map((e) => e.fecha)).size;
    if (!daysWithData) return null;
    const totalSoFar = monthEntries.reduce((s, e) => s + e.litros, 0);
    const avgPerDay = totalSoFar / daysWithData;
    const daysInMonth = new Date(y, m + 1, 0).getDate();
    const porProducto = PRODUCTOS.map((p) => {
      const soFar = monthEntries.filter((e) => e.producto === p).reduce((s, e) => s + e.litros, 0);
      const avg = soFar / daysWithData;
      return { producto: p, soFar, projected: avg * daysInMonth };
    });
    return { year: y, month: m, daysWithData, daysInMonth, totalSoFar, avgPerDay, projected: avgPerDay * daysInMonth, porProducto };
  }, [withYear, selectedMonth]);

  // "monthly" siempre usa el año completo — no se filtra por el selector de mes.
  const monthlyTotals = useMemo(() => {
    const t = { 2025: { litros: 0 }, 2026: { litros: 0 } };
    withYear.forEach((e) => { if (t[e.year]) t[e.year].litros += e.litros; });
    return t;
  }, [withYear]);

  const monthly = useMemo(() => {
    return MESES.map((mes, i) => {
      const row = { mes };
      YEARS.forEach((y) => {
        const val = withYear.filter((e) => e.year === y && e.month === i).reduce((s, e) => s + e.litros, 0);
        row[y] = val;
        row[`${y}pct`] = monthlyTotals[y].litros ? (val / monthlyTotals[y].litros) * 100 : 0;
      });
      return row;
    });
  }, [withYear, monthlyTotals]);

  // El resto (totales, producto, turno, mix) respeta el mes elegido en el selector.
  const scoped = useMemo(() => (
    selectedMonth === null ? withYear : withYear.filter((e) => e.month === selectedMonth)
  ), [withYear, selectedMonth]);

  const totals = useMemo(() => {
    const t = { 2025: { litros: 0, importe: 0 }, 2026: { litros: 0, importe: 0 } };
    scoped.forEach((e) => {
      if (t[e.year]) { t[e.year].litros += e.litros; t[e.year].importe += e.importe; }
    });
    return t;
  }, [scoped]);

  const yearComparison = useMemo(() => {
    const l25 = totals[2025].litros, l26 = totals[2026].litros;
    if (!l25 && !l26) return null;
    if (l26 >= l25) {
      const pct = l25 ? ((l26 - l25) / l25) * 100 : 100;
      return { winner: 2026, loser: 2025, pct };
    }
    const pct = l26 ? ((l25 - l26) / l26) * 100 : 100;
    return { winner: 2025, loser: 2026, pct };
  }, [totals]);

  const byProduct = useMemo(() => {
    return PRODUCTOS.map((p) => {
      const row = { producto: p === "Nafta Súper" ? "Súper" : p };
      YEARS.forEach((y) => {
        const val = scoped.filter((e) => e.producto === p && e.year === y).reduce((s, e) => s + e.litros, 0);
        row[y] = val;
        row[`${y}pct`] = totals[y].litros ? (val / totals[y].litros) * 100 : 0;
      });
      return row;
    });
  }, [scoped, totals]);

  const byTurno = useMemo(() => {
    return TURNOS.map((t) => {
      const row = { turno: t };
      YEARS.forEach((y) => {
        const val = scoped.filter((e) => e.turno === t && e.year === y).reduce((s, e) => s + e.litros, 0);
        row[y] = val;
        row[`${y}pct`] = totals[y].litros ? (val / totals[y].litros) * 100 : 0;
      });
      row.combinado = row[2025] + row[2026];
      return row;
    });
  }, [scoped, totals]);

  const turnoChange = useMemo(() => {
    return byTurno.map((r) => {
      let pct = null;
      if (r[2025] > 0) pct = ((r[2026] - r[2025]) / r[2025]) * 100;
      else if (r[2026] > 0) pct = 100;
      return { turno: r.turno, pct };
    });
  }, [byTurno]);

  function mixFor(list, year) {
    const data = list.map((p) => ({
      name: p, value: scoped.filter((e) => e.producto === p && e.year === year).reduce((s, e) => s + e.litros, 0),
    })).filter((d) => d.value > 0);
    return data;
  }
  const mixNaftas25 = useMemo(() => mixFor(NAFTAS, 2025), [scoped]);
  const mixNaftas26 = useMemo(() => mixFor(NAFTAS, 2026), [scoped]);
  const mixDiesel25 = useMemo(() => mixFor(DIESELS, 2025), [scoped]);
  const mixDiesel26 = useMemo(() => mixFor(DIESELS, 2026), [scoped]);

  const filteredEntries = useMemo(() => {
    return entries.filter((e) => {
      const year = String(e.fecha).slice(0, 4);
      const month = new Date(e.fecha + "T00:00:00").getMonth();
      if (filterYear !== "todos" && year !== String(filterYear)) return false;
      if (filterMonth !== null && month !== filterMonth) return false;
      return true;
    });
  }, [entries, filterYear, filterMonth]);

  const recent = [...filteredEntries].sort((a, b) => (a.fecha < b.fecha ? 1 : -1)).slice(0, 50);

  const dailyGroups = useMemo(() => {
    const byDate = {};
    filteredEntries.forEach((e) => {
      if (!byDate[e.fecha]) byDate[e.fecha] = {};
      if (!byDate[e.fecha][e.turno]) byDate[e.fecha][e.turno] = { litros: 0, importe: 0, ids: [] };
      byDate[e.fecha][e.turno].litros += e.litros;
      byDate[e.fecha][e.turno].importe += e.importe;
      byDate[e.fecha][e.turno].ids.push(e.id);
    });
    return Object.entries(byDate)
      .map(([fecha, turnos]) => ({
        fecha,
        total: Object.values(turnos).reduce((s, t) => s + t.litros, 0),
        turnos: TURNOS.filter((t) => turnos[t]).map((t) => ({ turno: t, ...turnos[t] })),
      }))
      .sort((a, b) => (a.fecha < b.fecha ? 1 : -1));
  }, [filteredEntries]);

  function toggleDate(fecha) {
    setExpandedDates((prev) => {
      const next = new Set(prev);
      if (next.has(fecha)) next.delete(fecha); else next.add(fecha);
      return next;
    });
  }

  function removeByIds(ids) {
    const idSet = new Set(ids);
    persist(entries.filter((x) => !idSet.has(x.id)));
  }

  // ---- Tienda: cargar ----
  const filteredTiendaEntries = useMemo(() => {
    return tiendaEntries.filter((e) => {
      const year = String(e.fecha).slice(0, 4);
      const month = new Date(e.fecha + "T00:00:00").getMonth();
      if (tiendaFilterYear !== "todos" && year !== String(tiendaFilterYear)) return false;
      if (tiendaFilterMonth !== null && month !== tiendaFilterMonth) return false;
      return true;
    });
  }, [tiendaEntries, tiendaFilterYear, tiendaFilterMonth]);

  function categoriaGrupo(categoria) {
    if (/^comidas?\s*(envasad|elaborad)/i.test(categoria)) return "comida";
    if (/^bebidas?\s*calient/i.test(categoria)) return "cafe";
    if (/^bebidas?\s*sin\s*alc/i.test(categoria)) return "bebida";
    if (/^cigarrill/i.test(categoria)) return "cigarrillos";
    return null;
  }

  const tiendaDailyGroups = useMemo(() => {
    const byDate = {};
    filteredTiendaEntries.forEach((e) => {
      if (!byDate[e.fecha]) byDate[e.fecha] = {};
      if (!byDate[e.fecha][e.turno]) {
        byDate[e.fecha][e.turno] = { comida: 0, cafe: 0, bebida: 0, cigarrillos: 0, ids: [] };
      }
      const grupo = categoriaGrupo(e.categoria);
      if (grupo) byDate[e.fecha][e.turno][grupo] += e.cantidad || 0;
      byDate[e.fecha][e.turno].ids.push(e.id);
    });
    return Object.entries(byDate)
      .map(([fecha, turnos]) => ({
        fecha,
        turnos: TURNOS_TIENDA.filter((t) => turnos[t]).map((t) => ({ turno: t, ...turnos[t] })),
      }))
      .sort((a, b) => (a.fecha < b.fecha ? 1 : -1));
  }, [filteredTiendaEntries]);

  function toggleTiendaDate(fecha) {
    setTiendaExpandedDates((prev) => {
      const next = new Set(prev);
      if (next.has(fecha)) next.delete(fecha); else next.add(fecha);
      return next;
    });
  }

  // ---- Tienda: comparativo ----
  const GRUPOS_TIENDA = ["comida", "cafe", "bebida", "cigarrillos"];
  const GRUPO_LABEL = { comida: "Comida", cafe: "Café", bebida: "Bebida", cigarrillos: "Cigarrillos" };

  const tiendaWithYear = useMemo(() => tiendaEntries.map((e) => ({
    ...e, year: parseInt(String(e.fecha).slice(0, 4), 10),
    month: new Date(e.fecha + "T00:00:00").getMonth(),
    grupo: categoriaGrupo(e.categoria),
  })), [tiendaEntries]);

  const tiendaScoped = useMemo(() => (
    tiendaSelectedMonth === null ? tiendaWithYear : tiendaWithYear.filter((e) => e.month === tiendaSelectedMonth)
  ), [tiendaWithYear, tiendaSelectedMonth]);

  const tiendaTotals = useMemo(() => {
    const t = {
      2025: { comida: 0, cafe: 0, bebida: 0, cigarrillos: 0, total: 0 },
      2026: { comida: 0, cafe: 0, bebida: 0, cigarrillos: 0, total: 0 },
    };
    tiendaScoped.forEach((e) => {
      if (t[e.year] && e.grupo) { t[e.year][e.grupo] += e.cantidad || 0; t[e.year].total += e.cantidad || 0; }
    });
    return t;
  }, [tiendaScoped]);

  const tiendaYearComparison = useMemo(() => {
    const a25 = tiendaTotals[2025].total, a26 = tiendaTotals[2026].total;
    if (!a25 && !a26) return null;
    if (a26 >= a25) {
      const pct = a25 ? ((a26 - a25) / a25) * 100 : 100;
      return { winner: 2026, loser: 2025, pct };
    }
    const pct = a26 ? ((a25 - a26) / a26) * 100 : 100;
    return { winner: 2025, loser: 2026, pct };
  }, [tiendaTotals]);

  const tiendaMonthly = useMemo(() => {
    return MESES.map((mes, i) => {
      const row = { mes };
      YEARS.forEach((y) => {
        row[y] = tiendaWithYear
          .filter((e) => e.year === y && e.month === i && e.grupo)
          .reduce((s, e) => s + (e.cantidad || 0), 0);
      });
      return row;
    });
  }, [tiendaWithYear]);

  const tiendaByTurno = useMemo(() => {
    return TURNOS_TIENDA.map((t) => {
      const row = { turno: t };
      YEARS.forEach((y) => {
        const val = tiendaScoped.filter((e) => e.turno === t && e.year === y && e.grupo).reduce((s, e) => s + (e.cantidad || 0), 0);
        row[y] = val;
        row[`${y}pct`] = tiendaTotals[y].total ? (val / tiendaTotals[y].total) * 100 : 0;
      });
      return row;
    });
  }, [tiendaScoped, tiendaTotals]);

  const tiendaTurnoChange = useMemo(() => {
    return tiendaByTurno.map((r) => {
      let pct = null;
      if (r[2025] > 0) pct = ((r[2026] - r[2025]) / r[2025]) * 100;
      else if (r[2026] > 0) pct = 100;
      return { turno: r.turno, pct };
    });
  }, [tiendaByTurno]);

  const tiendaByCategoria = useMemo(() => {
    const t25 = tiendaTotals[2025].total, t26 = tiendaTotals[2026].total;
    return GRUPOS_TIENDA.map((g) => {
      const v25 = tiendaTotals[2025][g], v26 = tiendaTotals[2026][g];
      return {
        categoria: GRUPO_LABEL[g], v25, v26,
        p25: t25 ? (v25 / t25) * 100 : 0, p26: t26 ? (v26 / t26) * 100 : 0,
      };
    });
  }, [tiendaTotals]);

  const tabBtn = (key, label) => (
    <button onClick={() => setTab(key)} style={{
      fontFamily: "'Oswald', sans-serif", fontSize: 14, letterSpacing: 1, textTransform: "uppercase",
      padding: "10px 20px", borderRadius: 8, border: `1px solid ${tab === key ? THEME.amber : THEME.border}`,
      background: tab === key ? THEME.amberDim : "transparent",
      color: tab === key ? THEME.amber : THEME.inkDim, cursor: "pointer", fontWeight: 600,
      transition: "all 0.15s",
    }}>{label}</button>
  );

  return (
    <div style={{
      background: THEME.bg, minHeight: "100%", color: THEME.ink,
      fontFamily: "'Inter', sans-serif", padding: "0 0 40px 0",
    }}>
      {/* header */}
      <div style={{
        borderBottom: `1px solid ${THEME.border}`, padding: "22px 24px",
        display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 40, height: 40, borderRadius: 8, background: THEME.amberDim,
            display: "flex", alignItems: "center", justifyContent: "center", border: `1px solid ${THEME.amber}55`,
          }}>{section === "tienda" ? <ShoppingBag size={20} color={THEME.amber} /> : <Fuel size={20} color={THEME.amber} />}</div>
          <div>
            <div style={{ fontFamily: "'Oswald', sans-serif", fontSize: 20, fontWeight: 700, letterSpacing: 0.5 }}>
              {section === "tienda" ? "TIENDA FULL — FARMEX" : "VENTAS DE COMBUSTIBLE — FARMEX"}
            </div>
            <div style={{ fontSize: 12, color: THEME.inkDim }}>Estación de servicio — comparativo 2025 / 2026</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {tabBtn("cargar", "Cargar")}
          {tabBtn("dashboard", "Comparativo")}
        </div>
      </div>

      <div style={{
        display: "flex", gap: 8, padding: "14px 24px 0",
      }}>
        <button onClick={() => setSection("combustible")} style={{
          fontFamily: "'Oswald', sans-serif", fontSize: 12, letterSpacing: 1, textTransform: "uppercase",
          padding: "7px 16px", borderRadius: 20, border: `1px solid ${section === "combustible" ? THEME.amber : THEME.border}`,
          background: section === "combustible" ? THEME.amberDim : "transparent",
          color: section === "combustible" ? THEME.amber : THEME.inkDim, cursor: "pointer", fontWeight: 600,
          display: "flex", alignItems: "center", gap: 6,
        }}><Fuel size={13} /> Combustible</button>
        <button onClick={() => setSection("tienda")} style={{
          fontFamily: "'Oswald', sans-serif", fontSize: 12, letterSpacing: 1, textTransform: "uppercase",
          padding: "7px 16px", borderRadius: 20, border: `1px solid ${section === "tienda" ? THEME.amber : THEME.border}`,
          background: section === "tienda" ? THEME.amberDim : "transparent",
          color: section === "tienda" ? THEME.amber : THEME.inkDim, cursor: "pointer", fontWeight: 600,
          display: "flex", alignItems: "center", gap: 6,
        }}><ShoppingBag size={13} /> Tienda Full</button>
      </div>

      <div style={{ padding: "24px" }}>
        {section === "combustible" && tab === "cargar" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 20, maxWidth: 1000, margin: "0 auto" }}>
            <Card>
              <SectionTitle icon={Upload}>Carga diaria (planilla o CSV)</SectionTitle>
              <p style={{ fontSize: 13, color: THEME.inkDim, lineHeight: 1.6 }}>
                Subí la planilla del aforador tal cual la generás (.xlsx) o un CSV con columnas
                <code style={codeStyle(THEME)}> fecha, turno, producto, litros, importe</code>.
                Los días y turnos que ya estén cargados se detectan solos y no se duplican —
                podés volver a subir el mismo archivo del mes cada día, sin filtrar nada a mano.
              </p>
              <input type="file" accept=".csv,.xlsx,.xls" onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])}
                style={{ ...inputStyle(THEME), padding: 10 }} />
              <button onClick={downloadTemplate} style={{ ...secondaryBtn(THEME), marginTop: 12, display: "flex", alignItems: "center", gap: 6 }}>
                <Download size={14} /> Descargar plantilla CSV
              </button>
              {importMsg && <div style={{ marginTop: 12, fontSize: 13, color: THEME.amber }}>{importMsg}</div>}
            </Card>

            <Card style={{ padding: 0 }}>
              <button onClick={() => setShowManualForm((v) => !v)} style={{
                width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between",
                background: "none", border: "none", cursor: "pointer", padding: 20, color: THEME.ink,
              }}>
                <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <Plus size={16} color={THEME.amber} />
                  <span style={{ fontFamily: "'Oswald', sans-serif", fontSize: 15, letterSpacing: 1, textTransform: "uppercase", fontWeight: 600 }}>
                    Cargar una venta manualmente
                  </span>
                </span>
                {showManualForm ? <ChevronDown size={16} color={THEME.inkDim} /> : <ChevronRight size={16} color={THEME.inkDim} />}
              </button>
              {showManualForm && (
                <form onSubmit={addEntry} style={{ display: "flex", flexDirection: "column", gap: 12, padding: "0 20px 20px" }}>
                  <label style={fieldLabel(THEME)}>Fecha
                    <input type="date" value={form.fecha} onChange={(e) => setForm({ ...form, fecha: e.target.value })} style={inputStyle(THEME)} required />
                  </label>
                  <label style={fieldLabel(THEME)}>Turno
                    <select value={form.turno} onChange={(e) => setForm({ ...form, turno: e.target.value })} style={inputStyle(THEME)}>
                      {TURNOS.map((t) => <option key={t} value={t}>{t}</option>)}
                    </select>
                  </label>
                  <label style={fieldLabel(THEME)}>Producto
                    <select value={form.producto} onChange={(e) => setForm({ ...form, producto: e.target.value })} style={inputStyle(THEME)}>
                      {PRODUCTOS.map((p) => <option key={p} value={p}>{p}</option>)}
                    </select>
                  </label>
                  <div style={{ display: "flex", gap: 12 }}>
                    <label style={{ ...fieldLabel(THEME), flex: 1 }}>Litros
                      <input type="number" min="0" step="0.01" value={form.litros} onChange={(e) => setForm({ ...form, litros: e.target.value })} style={inputStyle(THEME)} required />
                    </label>
                    <label style={{ ...fieldLabel(THEME), flex: 1 }}>Importe ($)
                      <input type="number" min="0" step="0.01" value={form.importe} onChange={(e) => setForm({ ...form, importe: e.target.value })} style={inputStyle(THEME)} />
                    </label>
                  </div>
                  <button type="submit" style={primaryBtn(THEME)}>Agregar registro</button>
                </form>
              )}
            </Card>

            <Card>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 10, marginBottom: 4 }}>
                <SectionTitle>Registros cargados ({entries.length} en total)</SectionTitle>
                {entries.length > 0 && (
                  <button onClick={clearAll} style={{ ...secondaryBtn(THEME), display: "flex", alignItems: "center", gap: 6, color: THEME.naftaSuper, borderColor: THEME.naftaSuper + "55" }}>
                    <Trash2 size={14} /> Borrar todo
                  </button>
                )}
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", marginBottom: 14 }}>
                <span style={{ fontSize: 12, color: THEME.inkDim, textTransform: "uppercase", letterSpacing: 1 }}>Filtrar</span>
                <select value={filterYear} onChange={(e) => setFilterYear(e.target.value)} style={{ ...inputStyle(THEME), width: "auto", padding: "7px 10px" }}>
                  <option value="todos">Todos los años</option>
                  {YEARS.map((y) => <option key={y} value={y}>{y}</option>)}
                </select>
                <select value={filterMonth === null ? "todos" : filterMonth}
                  onChange={(e) => setFilterMonth(e.target.value === "todos" ? null : parseInt(e.target.value, 10))}
                  style={{ ...inputStyle(THEME), width: "auto", padding: "7px 10px" }}>
                  <option value="todos">Todos los meses</option>
                  {MESES.map((m, i) => <option key={m} value={i}>{m}</option>)}
                </select>
                {(filterYear !== "todos" || filterMonth !== null) && filteredEntries.length > 0 && (
                  <button onClick={clearFiltered} style={{ ...secondaryBtn(THEME), display: "flex", alignItems: "center", gap: 6, color: THEME.naftaSuper, borderColor: THEME.naftaSuper + "55" }}>
                    <Trash2 size={14} /> Borrar {filteredEntries.length} de este filtro
                  </button>
                )}
              </div>

              {loading ? (
                <div style={{ color: THEME.inkDim, fontSize: 13 }}>Cargando datos guardados…</div>
              ) : dailyGroups.length === 0 ? (
                <div style={{ color: THEME.inkDim, fontSize: 13 }}>
                  {entries.length === 0 ? "Todavía no cargaste ninguna venta." : "No hay registros para ese filtro."}
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {dailyGroups.map((day) => {
                    const isOpen = expandedDates.has(day.fecha);
                    return (
                      <div key={day.fecha} style={{ border: `1px solid ${THEME.border}`, borderRadius: 8, overflow: "hidden" }}>
                        <button onClick={() => toggleDate(day.fecha)} style={{
                          width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between",
                          background: THEME.surfaceLight, border: "none", padding: "10px 14px", cursor: "pointer", color: THEME.ink,
                        }}>
                          <span style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, fontWeight: 600 }}>
                            {isOpen ? <ChevronDown size={15} color={THEME.inkDim} /> : <ChevronRight size={15} color={THEME.inkDim} />}
                            {day.fecha}
                          </span>
                          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 13, color: THEME.amber }}>
                            {fmtGrouped(day.total)} L
                          </span>
                        </button>
                        {isOpen && (
                          <div>
                            {day.turnos.map((t) => {
                              const Icon = TURNO_ICON[t.turno];
                              return (
                                <div key={t.turno} style={{
                                  display: "flex", alignItems: "center", justifyContent: "space-between",
                                  padding: "8px 14px", borderTop: `1px solid ${THEME.border}55`, fontSize: 13,
                                }}>
                                  <span style={{ display: "flex", alignItems: "center", gap: 8, color: THEME.inkDim }}>
                                    <Icon size={14} /> {t.turno}
                                  </span>
                                  <span style={{ display: "flex", alignItems: "center", gap: 14 }}>
                                    <span>{fmtGrouped(t.litros)} L</span>
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                  {filteredEntries.length > 0 && dailyGroups.length > 0 && (
                    <div style={{ fontSize: 12, color: THEME.inkDim, marginTop: 6 }}>
                      {dailyGroups.length} días — {filteredEntries.length} registros de detalle en total con este filtro.
                    </div>
                  )}
                </div>
              )}
            </Card>
          </div>
        )}

        {section === "combustible" && tab === "dashboard" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 20, maxWidth: 1100, margin: "0 auto" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <span style={{ fontSize: 12, color: THEME.inkDim, textTransform: "uppercase", letterSpacing: 1 }}>Ver mes</span>
              <select value={selectedMonth === null ? "todos" : selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value === "todos" ? null : parseInt(e.target.value, 10))}
                style={{ ...inputStyle(THEME), width: "auto", padding: "7px 10px" }}>
                <option value="todos">Todos los meses</option>
                {MESES.map((m, i) => <option key={m} value={i}>{m}</option>)}
              </select>
              <span style={{ fontSize: 12, color: THEME.inkDim }}>
                {selectedMonth === null
                  ? "— totales, mix y comparaciones de todo el período cargado"
                  : `— totales, mix y comparaciones solo de ${MESES[selectedMonth]}`}
              </span>
            </div>

            <div className="grid md:grid-cols-2" style={{ display: "grid", gridTemplateColumns: "1fr", gap: 20 }}>
              {YEARS.map((y) => (
                <Card key={y}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
                    <div style={{ fontFamily: "'Oswald', sans-serif", fontSize: 13, color: THEME.inkDim, letterSpacing: 1 }}>AÑO {y}</div>
                    {yearComparison && yearComparison.loser === y && (
                      <div style={{
                        fontSize: 11, fontWeight: 700, color: THEME.naftaSuper, background: THEME.naftaSuper + "22",
                        border: `1px solid ${THEME.naftaSuper}55`, borderRadius: 20, padding: "3px 10px",
                      }}>▼ Vendió menos (-{yearComparison.pct.toFixed(1)}%)</div>
                    )}
                  </div>
                  <PumpNumber value={totals[y].litros} label="Litros vendidos" color={YEAR_COLORS[y]} />
                </Card>
              ))}
            </div>

            {selectedMonth !== null && !monthProjection && (
              <Card>
                <SectionTitle icon={TrendingUp}>Proyección — {MESES[selectedMonth]}</SectionTitle>
                <p style={{ fontSize: 13, color: THEME.inkDim }}>Todavía no hay días cargados de {MESES[selectedMonth]} para proyectar.</p>
              </Card>
            )}

            {monthProjection && (
              <Card>
                <SectionTitle icon={TrendingUp}>Proyección — {MESES[monthProjection.month]} {monthProjection.year}</SectionTitle>
                <p style={{ fontSize: 12, color: THEME.inkDim, marginBottom: 16 }}>
                  Con {monthProjection.daysWithData} día{monthProjection.daysWithData !== 1 ? "s" : ""} cargado{monthProjection.daysWithData !== 1 ? "s" : ""} de {monthProjection.daysInMonth} del mes,
                  a este ritmo el mes cerraría en:
                </p>
                <div className="grid md:grid-cols-2" style={{ display: "grid", gridTemplateColumns: "1fr", gap: 24 }}>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 32 }}>
                    <PumpNumber value={monthProjection.totalSoFar} label="Litros hasta ahora" color={THEME.inkDim} />
                    <PumpNumber value={monthProjection.avgPerDay} label="Promedio diario" color={THEME.inkDim} />
                    <PumpNumber value={monthProjection.projected} label="Proyección fin de mes" color={THEME.amber} />
                  </div>
                  <div>
                    <div style={{ fontSize: 11, color: THEME.inkDim, textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>
                      Proyección por producto
                    </div>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                      <tbody>
                        {monthProjection.porProducto.map((r) => (
                          <tr key={r.producto} style={{ borderBottom: `1px solid ${THEME.border}55` }}>
                            <td style={{ ...td, paddingLeft: 0 }}>
                              <span style={{ color: PRODUCT_COLOR[r.producto] }}>●</span> {r.producto}
                            </td>
                            <td style={{ ...td, textAlign: "right", color: THEME.inkDim, fontSize: 11 }}>
                              {fmtGrouped(r.soFar)} L hasta ahora
                            </td>
                            <td style={{ ...td, textAlign: "right", fontWeight: 700, color: THEME.amber }}>
                              {fmtGrouped(r.projected)} L
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </Card>
            )}

            <Card>
              <SectionTitle>Venta total por mes — 2025 vs 2026 (litros)</SectionTitle>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={monthly}>
                  <CartesianGrid stroke={THEME.border} strokeDasharray="3 3" />
                  <XAxis dataKey="mes" stroke={THEME.inkDim} fontSize={12} />
                  <YAxis stroke={THEME.inkDim} fontSize={12} />
                  <Tooltip contentStyle={tooltipStyle(THEME)} formatter={(v) => `${fmtGrouped(v)} L`} />
                  <Legend />
                  <Bar dataKey="2025" fill={YEAR_COLORS[2025]} radius={[3, 3, 0, 0]} />
                  <Bar dataKey="2026" fill={YEAR_COLORS[2026]} radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>

            <div className="grid md:grid-cols-2" style={{ display: "grid", gridTemplateColumns: "1fr", gap: 20 }}>
              <Card>
                <SectionTitle>Venta por producto (litros){selectedMonth !== null ? ` — ${MESES[selectedMonth]}` : ""}</SectionTitle>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={byProduct} layout="vertical" margin={{ left: 10, right: 30 }}>
                    <CartesianGrid stroke={THEME.border} strokeDasharray="3 3" />
                    <XAxis type="number" stroke={THEME.inkDim} fontSize={12} />
                    <YAxis type="category" dataKey="producto" stroke={THEME.inkDim} fontSize={12} width={70} />
                    <Tooltip contentStyle={tooltipStyle(THEME)} formatter={(v) => `${fmtGrouped(v)} L`} />
                    <Legend />
                    <Bar dataKey="2025" fill={YEAR_COLORS[2025]} radius={[0, 3, 3, 0]}>
                      <LabelList dataKey="2025pct" position="right" formatter={(v) => `${v.toFixed(0)}%`} fill={THEME.ink} fontSize={12} fontWeight={700} />
                    </Bar>
                    <Bar dataKey="2026" fill={YEAR_COLORS[2026]} radius={[0, 3, 3, 0]}>
                      <LabelList dataKey="2026pct" position="right" formatter={(v) => `${v.toFixed(0)}%`} fill={THEME.ink} fontSize={12} fontWeight={700} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Card>

              <Card>
                <SectionTitle>Venta por turno (litros){selectedMonth !== null ? ` — ${MESES[selectedMonth]}` : ""}</SectionTitle>
                <div style={{ display: "flex", gap: 14, flexWrap: "wrap", marginTop: -8, marginBottom: 10 }}>
                  {turnoChange.map((r) => (
                    <span key={r.turno} style={{ fontSize: 12, fontWeight: 600, color: THEME.inkDim }}>
                      {r.turno}:{" "}
                      {r.pct === null ? (
                        <span style={{ color: THEME.inkDim }}>sin datos</span>
                      ) : (
                        <span style={{ color: r.pct >= 0 ? THEME.diesel : THEME.naftaSuper }}>
                          {r.pct >= 0 ? "▲" : "▼"} {r.pct >= 0 ? "+" : ""}{r.pct.toFixed(1)}%
                        </span>
                      )}
                    </span>
                  ))}
                </div>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={byTurno} margin={{ top: 24 }}>
                    <CartesianGrid stroke={THEME.border} strokeDasharray="3 3" />
                    <XAxis dataKey="turno" stroke={THEME.inkDim} fontSize={12} />
                    <YAxis stroke={THEME.inkDim} fontSize={12} />
                    <Tooltip content={<TurnoTooltip />} />
                    <Legend />
                    <Bar dataKey="2025" fill={YEAR_COLORS[2025]} radius={[3, 3, 0, 0]}>
                      <LabelList dataKey="2025pct" position="top" formatter={(v) => `${v.toFixed(0)}%`} fill={THEME.ink} fontSize={12} fontWeight={700} />
                    </Bar>
                    <Bar dataKey="2026" fill={YEAR_COLORS[2026]} radius={[3, 3, 0, 0]}>
                      <LabelList dataKey="2026pct" position="top" formatter={(v) => `${v.toFixed(0)}%`} fill={THEME.ink} fontSize={12} fontWeight={700} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </div>

            <Card>
              <SectionTitle icon={Droplet}>Mix de productos{selectedMonth !== null ? ` — ${MESES[selectedMonth]}` : ""}</SectionTitle>
              {(() => {
                const sumOf = (data) => data.reduce((s, d) => s + d.value, 0);
                const rowsFor = (list25, list26) => {
                  const t25 = sumOf(list25), t26 = sumOf(list26);
                  const names = [...new Set([...list25.map((d) => d.name), ...list26.map((d) => d.name)])];
                  return names.map((name) => {
                    const v25 = list25.find((d) => d.name === name)?.value || 0;
                    const v26 = list26.find((d) => d.name === name)?.value || 0;
                    return {
                      name, v25, v26,
                      p25: t25 ? (v25 / t25) * 100 : 0,
                      p26: t26 ? (v26 / t26) * 100 : 0,
                    };
                  });
                };
                const naftaRows = rowsFor(mixNaftas25, mixNaftas26);
                const dieselRows = rowsFor(mixDiesel25, mixDiesel26);
                const allEmpty = naftaRows.every((r) => !r.v25 && !r.v26) && dieselRows.every((r) => !r.v25 && !r.v26);

                if (allEmpty) return <div style={{ color: THEME.inkDim, fontSize: 13 }}>Sin datos para este período.</div>;

                const Row = ({ r }) => (
                  <tr style={{ borderBottom: `1px solid ${THEME.border}55` }}>
                    <td style={td}><span style={{ color: PRODUCT_COLOR[r.name] }}>●</span> {r.name}</td>
                    <td style={{ ...td, color: YEAR_COLORS[2025] }}>{r.p25.toFixed(0)}%</td>
                    <td style={{ ...td, fontSize: 11, color: THEME.inkDim }}>{fmtGrouped(r.v25)} L</td>
                    <td style={{ ...td, color: YEAR_COLORS[2026] }}>{r.p26.toFixed(0)}%</td>
                    <td style={{ ...td, fontSize: 11, color: THEME.inkDim }}>{fmtGrouped(r.v26)} L</td>
                  </tr>
                );

                return (
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                    <thead>
                      <tr style={{ color: THEME.inkDim, textAlign: "left", borderBottom: `1px solid ${THEME.border}` }}>
                        <th style={th}>Producto</th>
                        <th style={{ ...th, color: YEAR_COLORS[2025] }}>% 2025</th>
                        <th style={th}></th>
                        <th style={{ ...th, color: YEAR_COLORS[2026] }}>% 2026</th>
                        <th style={th}></th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr><td colSpan={5} style={{ ...td, fontSize: 11, color: THEME.inkDim, textTransform: "uppercase", letterSpacing: 1, paddingTop: 14 }}>Naftas</td></tr>
                      {naftaRows.map((r) => <Row key={r.name} r={r} />)}
                      <tr><td colSpan={5} style={{ ...td, fontSize: 11, color: THEME.inkDim, textTransform: "uppercase", letterSpacing: 1, paddingTop: 14 }}>Diesel</td></tr>
                      {dieselRows.map((r) => <Row key={r.name} r={r} />)}
                    </tbody>
                  </table>
                );
              })()}
            </Card>
          </div>
        )}

        {section === "tienda" && tab === "cargar" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 20, maxWidth: 1000, margin: "0 auto" }}>
            <Card>
              <SectionTitle icon={Upload}>Carga diaria — Tienda Full</SectionTitle>
              <p style={{ fontSize: 13, color: THEME.inkDim, lineHeight: 1.6 }}>
                Subí el reporte de cierre de caja tal cual lo generás (.htm) — el nombre del archivo debe
                terminar en <code style={codeStyle(THEME)}>TM</code> o <code style={codeStyle(THEME)}>TT</code> según el turno
                (ej: <code style={codeStyle(THEME)}>31-07__TM.htm</code>). La fecha y los rubros se leen solos del reporte.
                También podés subir un CSV con columnas <code style={codeStyle(THEME)}>fecha, turno, categoria, importe</code>.
                Los días y turnos ya cargados se detectan solos y no se duplican.
              </p>
              <input type="file" accept=".csv,.htm,.html" onChange={(e) => e.target.files[0] && handleTiendaFile(e.target.files[0])}
                style={{ ...inputStyle(THEME), padding: 10 }} />
              <button onClick={downloadTiendaTemplate} style={{ ...secondaryBtn(THEME), marginTop: 12, display: "flex", alignItems: "center", gap: 6 }}>
                <Download size={14} /> Descargar plantilla CSV
              </button>
              {tiendaImportMsg && <div style={{ marginTop: 12, fontSize: 13, color: THEME.amber }}>{tiendaImportMsg}</div>}
            </Card>

            <Card style={{ padding: 0 }}>
              <button onClick={() => setTiendaShowManualForm((v) => !v)} style={{
                width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between",
                background: "none", border: "none", cursor: "pointer", padding: 20, color: THEME.ink,
              }}>
                <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <Plus size={16} color={THEME.amber} />
                  <span style={{ fontFamily: "'Oswald', sans-serif", fontSize: 15, letterSpacing: 1, textTransform: "uppercase", fontWeight: 600 }}>
                    Cargar una venta manualmente
                  </span>
                </span>
                {tiendaShowManualForm ? <ChevronDown size={16} color={THEME.inkDim} /> : <ChevronRight size={16} color={THEME.inkDim} />}
              </button>
              {tiendaShowManualForm && (
                <form onSubmit={addTiendaEntry} style={{ display: "flex", flexDirection: "column", gap: 12, padding: "0 20px 20px" }}>
                  <label style={fieldLabel(THEME)}>Fecha
                    <input type="date" value={tiendaForm.fecha} onChange={(e) => setTiendaForm({ ...tiendaForm, fecha: e.target.value })} style={inputStyle(THEME)} required />
                  </label>
                  <label style={fieldLabel(THEME)}>Turno
                    <select value={tiendaForm.turno} onChange={(e) => setTiendaForm({ ...tiendaForm, turno: e.target.value })} style={inputStyle(THEME)}>
                      {TURNOS_TIENDA.map((t) => <option key={t} value={t}>{t}</option>)}
                    </select>
                  </label>
                  <label style={fieldLabel(THEME)}>Categoría / producto
                    <input type="text" placeholder="Ej: Kiosco, Café, Panadería…" value={tiendaForm.categoria}
                      onChange={(e) => setTiendaForm({ ...tiendaForm, categoria: e.target.value })} style={inputStyle(THEME)} required />
                  </label>
                  <label style={fieldLabel(THEME)}>Importe ($)
                    <input type="number" min="0" step="0.01" value={tiendaForm.importe} onChange={(e) => setTiendaForm({ ...tiendaForm, importe: e.target.value })} style={inputStyle(THEME)} required />
                  </label>
                  <button type="submit" style={primaryBtn(THEME)}>Agregar registro</button>
                </form>
              )}
            </Card>

            <Card>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 10, marginBottom: 4 }}>
                <SectionTitle>Registros cargados ({tiendaEntries.length} en total)</SectionTitle>
                {tiendaEntries.length > 0 && (
                  <button onClick={clearAllTienda} style={{ ...secondaryBtn(THEME), display: "flex", alignItems: "center", gap: 6, color: THEME.naftaSuper, borderColor: THEME.naftaSuper + "55" }}>
                    <Trash2 size={14} /> Borrar todo
                  </button>
                )}
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", marginBottom: 14 }}>
                <span style={{ fontSize: 12, color: THEME.inkDim, textTransform: "uppercase", letterSpacing: 1 }}>Filtrar</span>
                <select value={tiendaFilterYear} onChange={(e) => setTiendaFilterYear(e.target.value)} style={{ ...inputStyle(THEME), width: "auto", padding: "7px 10px" }}>
                  <option value="todos">Todos los años</option>
                  {YEARS.map((y) => <option key={y} value={y}>{y}</option>)}
                </select>
                <select value={tiendaFilterMonth === null ? "todos" : tiendaFilterMonth}
                  onChange={(e) => setTiendaFilterMonth(e.target.value === "todos" ? null : parseInt(e.target.value, 10))}
                  style={{ ...inputStyle(THEME), width: "auto", padding: "7px 10px" }}>
                  <option value="todos">Todos los meses</option>
                  {MESES.map((m, i) => <option key={m} value={i}>{m}</option>)}
                </select>
                {(tiendaFilterYear !== "todos" || tiendaFilterMonth !== null) && filteredTiendaEntries.length > 0 && (
                  <button onClick={clearFilteredTienda} style={{ ...secondaryBtn(THEME), display: "flex", alignItems: "center", gap: 6, color: THEME.naftaSuper, borderColor: THEME.naftaSuper + "55" }}>
                    <Trash2 size={14} /> Borrar {filteredTiendaEntries.length} de este filtro
                  </button>
                )}
              </div>

              {tiendaLoading ? (
                <div style={{ color: THEME.inkDim, fontSize: 13 }}>Cargando datos guardados…</div>
              ) : tiendaDailyGroups.length === 0 ? (
                <div style={{ color: THEME.inkDim, fontSize: 13 }}>
                  {tiendaEntries.length === 0 ? "Todavía no cargaste ninguna venta de Tienda Full." : "No hay registros para ese filtro."}
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {tiendaDailyGroups.map((day) => {
                    const isOpen = tiendaExpandedDates.has(day.fecha);
                    return (
                      <div key={day.fecha} style={{ border: `1px solid ${THEME.border}`, borderRadius: 8, overflow: "hidden" }}>
                        <button onClick={() => toggleTiendaDate(day.fecha)} style={{
                          width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between",
                          background: THEME.surfaceLight, border: "none", padding: "10px 14px", cursor: "pointer", color: THEME.ink,
                        }}>
                          <span style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, fontWeight: 600 }}>
                            {isOpen ? <ChevronDown size={15} color={THEME.inkDim} /> : <ChevronRight size={15} color={THEME.inkDim} />}
                            {day.fecha}
                          </span>
                        </button>
                        {isOpen && (
                          <div>
                            {day.turnos.map((t) => {
                              const Icon = TURNO_ICON[t.turno];
                              return (
                                <div key={t.turno} style={{
                                  display: "flex", alignItems: "center", justifyContent: "space-between",
                                  padding: "8px 14px", borderTop: `1px solid ${THEME.border}55`, fontSize: 13, flexWrap: "wrap", gap: 8,
                                }}>
                                  <span style={{ display: "flex", alignItems: "center", gap: 8, color: THEME.inkDim }}>
                                    <Icon size={14} /> {t.turno}
                                  </span>
                                  <span style={{ display: "flex", gap: 16, fontSize: 12 }}>
                                    <span>Comida: <b>{fmtNum(t.comida)}</b></span>
                                    <span>Café: <b>{fmtNum(t.cafe)}</b></span>
                                    <span>Bebida: <b>{fmtNum(t.bebida)}</b></span>
                                    <span>Cigarrillos: <b>{fmtNum(t.cigarrillos)}</b></span>
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                  {filteredTiendaEntries.length > 0 && (
                    <div style={{ fontSize: 12, color: THEME.inkDim, marginTop: 6 }}>
                      {tiendaDailyGroups.length} días — {filteredTiendaEntries.length} registros de detalle en total con este filtro.
                    </div>
                  )}
                </div>
              )}
            </Card>
          </div>
        )}

        {section === "tienda" && tab === "dashboard" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 20, maxWidth: 1100, margin: "0 auto" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <span style={{ fontSize: 12, color: THEME.inkDim, textTransform: "uppercase", letterSpacing: 1 }}>Ver mes</span>
              <select value={tiendaSelectedMonth === null ? "todos" : tiendaSelectedMonth}
                onChange={(e) => setTiendaSelectedMonth(e.target.value === "todos" ? null : parseInt(e.target.value, 10))}
                style={{ ...inputStyle(THEME), width: "auto", padding: "7px 10px" }}>
                <option value="todos">Todos los meses</option>
                {MESES.map((m, i) => <option key={m} value={i}>{m}</option>)}
              </select>
            </div>

            <div className="grid md:grid-cols-2" style={{ display: "grid", gridTemplateColumns: "1fr", gap: 20 }}>
              {YEARS.map((y) => (
                <Card key={y}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
                    <div style={{ fontFamily: "'Oswald', sans-serif", fontSize: 13, color: THEME.inkDim, letterSpacing: 1 }}>AÑO {y}</div>
                    {tiendaYearComparison && tiendaYearComparison.loser === y && (
                      <div style={{
                        fontSize: 11, fontWeight: 700, color: THEME.naftaSuper, background: THEME.naftaSuper + "22",
                        border: `1px solid ${THEME.naftaSuper}55`, borderRadius: 20, padding: "3px 10px",
                      }}>▼ Vendió menos (-{tiendaYearComparison.pct.toFixed(1)}%)</div>
                    )}
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 24 }}>
                    {GRUPOS_TIENDA.map((g) => (
                      <PumpNumber key={g} value={tiendaTotals[y][g]} label={GRUPO_LABEL[g]} color={YEAR_COLORS[y]} />
                    ))}
                  </div>
                </Card>
              ))}
            </div>

            <Card>
              <SectionTitle>Unidades vendidas por mes — 2025 vs 2026</SectionTitle>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={tiendaMonthly}>
                  <CartesianGrid stroke={THEME.border} strokeDasharray="3 3" />
                  <XAxis dataKey="mes" stroke={THEME.inkDim} fontSize={12} />
                  <YAxis stroke={THEME.inkDim} fontSize={12} />
                  <Tooltip contentStyle={tooltipStyle(THEME)} formatter={(v) => `${fmtGrouped(v)} u.`} />
                  <Legend />
                  <Bar dataKey="2025" fill={YEAR_COLORS[2025]} radius={[3, 3, 0, 0]} />
                  <Bar dataKey="2026" fill={YEAR_COLORS[2026]} radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>

            <Card>
              <SectionTitle>Unidades por turno{tiendaSelectedMonth !== null ? ` — ${MESES[tiendaSelectedMonth]}` : ""}</SectionTitle>
              <div style={{ display: "flex", gap: 14, flexWrap: "wrap", marginTop: -8, marginBottom: 10 }}>
                {tiendaTurnoChange.map((r) => (
                  <span key={r.turno} style={{ fontSize: 12, fontWeight: 600, color: THEME.inkDim }}>
                    {r.turno}:{" "}
                    {r.pct === null ? (
                      <span style={{ color: THEME.inkDim }}>sin datos</span>
                    ) : (
                      <span style={{ color: r.pct >= 0 ? THEME.diesel : THEME.naftaSuper }}>
                        {r.pct >= 0 ? "▲" : "▼"} {r.pct >= 0 ? "+" : ""}{r.pct.toFixed(1)}%
                      </span>
                    )}
                  </span>
                ))}
              </div>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={tiendaByTurno} margin={{ top: 24 }}>
                  <CartesianGrid stroke={THEME.border} strokeDasharray="3 3" />
                  <XAxis dataKey="turno" stroke={THEME.inkDim} fontSize={12} />
                  <YAxis stroke={THEME.inkDim} fontSize={12} />
                  <Tooltip contentStyle={tooltipStyle(THEME)} formatter={(v) => `${fmtGrouped(v)} u.`} />
                  <Legend />
                  <Bar dataKey="2025" fill={YEAR_COLORS[2025]} radius={[3, 3, 0, 0]}>
                    <LabelList dataKey="2025pct" position="top" formatter={(v) => `${v.toFixed(0)}%`} fill={THEME.ink} fontSize={12} fontWeight={700} />
                  </Bar>
                  <Bar dataKey="2026" fill={YEAR_COLORS[2026]} radius={[3, 3, 0, 0]}>
                    <LabelList dataKey="2026pct" position="top" formatter={(v) => `${v.toFixed(0)}%`} fill={THEME.ink} fontSize={12} fontWeight={700} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>

            <Card>
              <SectionTitle icon={ShoppingBag}>Versus por rubro — 2025 vs 2026{tiendaSelectedMonth !== null ? ` (${MESES[tiendaSelectedMonth]})` : ""}</SectionTitle>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ color: THEME.inkDim, textAlign: "left", borderBottom: `1px solid ${THEME.border}` }}>
                    <th style={th}>Rubro</th>
                    <th style={{ ...th, color: YEAR_COLORS[2025] }}>% 2025</th>
                    <th style={th}></th>
                    <th style={{ ...th, color: YEAR_COLORS[2026] }}>% 2026</th>
                    <th style={th}></th>
                  </tr>
                </thead>
                <tbody>
                  {tiendaByCategoria.map((r) => (
                    <tr key={r.categoria} style={{ borderBottom: `1px solid ${THEME.border}55` }}>
                      <td style={td}>{r.categoria}</td>
                      <td style={{ ...td, color: YEAR_COLORS[2025] }}>{r.p25.toFixed(0)}%</td>
                      <td style={{ ...td, fontSize: 11, color: THEME.inkDim }}>{fmtGrouped(r.v25)} u.</td>
                      <td style={{ ...td, color: YEAR_COLORS[2026] }}>{r.p26.toFixed(0)}%</td>
                      <td style={{ ...td, fontSize: 11, color: THEME.inkDim }}>{fmtGrouped(r.v26)} u.</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {tiendaTotals[2025].total === 0 && (
                <div style={{ fontSize: 12, color: THEME.inkDim, marginTop: 10 }}>
                  Todavía no hay datos de 2025 para comparar — en cuanto me pases los reportes del año anterior, este cuadro arma el versus completo por rubro.
                </div>
              )}
            </Card>
          </div>
        )}
      </div>

      <div style={{ textAlign: "center", padding: "16px 24px 8px", fontSize: 11, color: THEME.inkDim }}>
        Desarrollado por Lucas Sellecchia
      </div>

      {showClearModal && (
        <div style={{
          position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
          display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50, padding: 20,
        }} onClick={() => setShowClearModal(false)}>
          <div onClick={(e) => e.stopPropagation()} style={{
            background: THEME.surface, border: `1px solid ${THEME.border}`, borderRadius: 10,
            padding: 24, width: "100%", maxWidth: 360,
          }}>
            <div style={{ fontFamily: "'Oswald', sans-serif", fontSize: 16, fontWeight: 700, marginBottom: 8 }}>
              Borrar registros
            </div>
            <p style={{ fontSize: 13, color: THEME.inkDim, marginBottom: 14, lineHeight: 1.5 }}>
              Esta acción borra {clearScopeLabel} y no se puede deshacer.
              Ingresá la clave para confirmar.
            </p>
            <input
              type="password" autoFocus value={clearPassword}
              onChange={(e) => { setClearPassword(e.target.value); setClearError(null); }}
              onKeyDown={(e) => { if (e.key === "Enter") confirmClearAll(); }}
              placeholder="Clave"
              style={inputStyle(THEME)}
            />
            {clearError && <div style={{ color: THEME.naftaSuper, fontSize: 12, marginTop: 8 }}>{clearError}</div>}
            <div style={{ display: "flex", gap: 10, marginTop: 18 }}>
              <button onClick={() => setShowClearModal(false)} style={{ ...secondaryBtn(THEME), flex: 1 }}>Cancelar</button>
              <button onClick={confirmClearAll} style={{
                flex: 1, background: THEME.naftaSuper, color: "#fff", border: "none", borderRadius: 6,
                padding: "9px 14px", cursor: "pointer", fontSize: 13, fontWeight: 700,
              }}>Borrar todo</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const th = { padding: "8px 10px", fontWeight: 500 };
const td = { padding: "8px 10px" };
function fieldLabel(T) { return { display: "flex", flexDirection: "column", gap: 6, fontSize: 12, color: T.inkDim, textTransform: "uppercase", letterSpacing: 0.5 }; }
function inputStyle(T) { return { background: "#081220", border: `1px solid ${T.border}`, borderRadius: 6, padding: "9px 10px", color: T.ink, fontSize: 14, fontFamily: "'Inter', sans-serif" }; }
function primaryBtn(T) { return { marginTop: 4, background: T.amber, color: "#071523", border: "none", borderRadius: 6, padding: "10px 16px", fontWeight: 700, fontFamily: "'Oswald', sans-serif", letterSpacing: 0.5, cursor: "pointer", fontSize: 14, textTransform: "uppercase" }; }
function secondaryBtn(T) { return { background: "transparent", color: T.ink, border: `1px solid ${T.border}`, borderRadius: 6, padding: "9px 14px", cursor: "pointer", fontSize: 13 }; }
function codeStyle(T) { return { background: "#081220", padding: "2px 6px", borderRadius: 4, fontSize: 12 }; }
function tooltipStyle(T) { return { background: T.surfaceLight, border: `1px solid ${T.border}`, borderRadius: 6, fontSize: 12, color: T.ink }; }

function TurnoTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  const v25 = payload.find((p) => p.dataKey === "2025")?.value || 0;
  const v26 = payload.find((p) => p.dataKey === "2026")?.value || 0;
  let pct = null;
  if (v25 > 0) pct = ((v26 - v25) / v25) * 100;
  else if (v26 > 0) pct = 100;
  return (
    <div style={{ ...tooltipStyle(THEME), padding: "10px 12px" }}>
      <div style={{ fontWeight: 700, marginBottom: 6 }}>{label}</div>
      <div style={{ color: YEAR_COLORS[2025] }}>2025: {fmtGrouped(v25)} L</div>
      <div style={{ color: YEAR_COLORS[2026] }}>2026: {fmtGrouped(v26)} L</div>
      {pct !== null && (
        <div style={{ marginTop: 4, fontWeight: 700, color: pct >= 0 ? THEME.diesel : THEME.naftaSuper }}>
          {pct >= 0 ? "▲" : "▼"} {pct >= 0 ? "+" : ""}{pct.toFixed(1)}% vs 2025
        </div>
      )}
    </div>
  );
}

function TiendaTurnoTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  const v25 = payload.find((p) => p.dataKey === "2025")?.value || 0;
  const v26 = payload.find((p) => p.dataKey === "2026")?.value || 0;
  let pct = null;
  if (v25 > 0) pct = ((v26 - v25) / v25) * 100;
  else if (v26 > 0) pct = 100;
  return (
    <div style={{ ...tooltipStyle(THEME), padding: "10px 12px" }}>
      <div style={{ fontWeight: 700, marginBottom: 6 }}>{label}</div>
      <div style={{ color: YEAR_COLORS[2025] }}>2025: {fmtMoney(v25)}</div>
      <div style={{ color: YEAR_COLORS[2026] }}>2026: {fmtMoney(v26)}</div>
      {pct !== null && (
        <div style={{ marginTop: 4, fontWeight: 700, color: pct >= 0 ? THEME.diesel : THEME.naftaSuper }}>
          {pct >= 0 ? "▲" : "▼"} {pct >= 0 ? "+" : ""}{pct.toFixed(1)}% vs 2025
        </div>
      )}
    </div>
  );
}
