import { ChatContainer } from "@/components/chat/chat-container";
import { redirect } from "next/navigation";
import { cookies } from "next/headers";

interface ChatPageProps {
  params: {
    sessionId: string;
  };
}

export default async function ChatPage({ params }: ChatPageProps) {
  const cookieStore = await cookies();
  const backendToken = cookieStore.get("backend_access_token");

  if (!backendToken) {
    redirect("/login");
  }

  const user = {
    name: "User",
    email: "",
  };

  return <ChatContainer user={user} initialSessionId={params.sessionId} />;
}

