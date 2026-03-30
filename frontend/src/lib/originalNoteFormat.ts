const MARK_ER = "---ER---";
const MARK_HP = "---H&P---";
const MARK_OTHER = "---OTHER---";

export function serializeOriginalNote(er: string, hp: string, other: string): string {
  return [MARK_ER, er.trim(), MARK_HP, hp.trim(), MARK_OTHER, other.trim()].join("\n\n");
}

export function deserializeOriginalNote(note: string): { er: string; hp: string; other: string } {
  const erI = note.indexOf(MARK_ER);
  const hpI = note.indexOf(MARK_HP);
  const otherI = note.indexOf(MARK_OTHER);
  if (erI === -1 || hpI === -1 || otherI === -1) {
    return { er: "", hp: "", other: note.trim() };
  }
  const er = note.slice(erI + MARK_ER.length, hpI).trim();
  const hp = note.slice(hpI + MARK_HP.length, otherI).trim();
  const other = note.slice(otherI + MARK_OTHER.length).trim();
  return { er, hp, other };
}

export function hasAnyClinicalInput(er: string, hp: string, other: string): boolean {
  return Boolean(er.trim() || hp.trim() || other.trim());
}
