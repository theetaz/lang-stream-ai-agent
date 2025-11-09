import { ChatContainer } from "@/components/chat/chat-container";
import { redirect } from "next/navigation";
import { cookies } from "next/headers";

interface ChatPageProps {
  params: Promise<{
    sessionId: string;
  }>;
}

export default async function ChatPage({ params }: ChatPageProps) {
  const cookieStore = await cookies();
  const backendToken = cookieStore.get("backend_access_token");

  if (!backendToken) {
    redirect("/login");
  }

  const { sessionId } = await params;

  const user = {
    name: "User",
    email: "",
  };

  return <ChatContainer user={user} initialSessionId={sessionId} />;
}

