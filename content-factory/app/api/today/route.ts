import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

const TODAY_JSON = path.join(process.cwd(), "src", "data", "today.json");

// GET /api/today — return current today.json
export async function GET() {
  if (!fs.existsSync(TODAY_JSON)) {
    return NextResponse.json({ error: "today.json not found" }, { status: 404 });
  }

  const raw = fs.readFileSync(TODAY_JSON, "utf-8");
  const data = JSON.parse(raw);
  return NextResponse.json(data);
}
