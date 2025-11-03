import { SessionsContainer } from "@/components/sessions/sessions-container";
import { redirect } from "next/navigation";
import { cookies } from "next/headers";

export default async function SessionsPage() {
  const cookieStore = await cookies();
  const backendToken = cookieStore.get("backend_access_token");

  if (!backendToken) {
    redirect("/login");
  }

  return <SessionsContainer />;
}
