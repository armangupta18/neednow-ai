import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    service: "NeedNow AI Frontend",
    status: "running",
  });
}
