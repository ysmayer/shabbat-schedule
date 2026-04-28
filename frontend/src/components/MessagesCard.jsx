export default function MessagesCard({ messages }) {
  if (!messages || !messages.trim()) return null;
  return (
    <div className="messages-card area-messages" style={{ display: 'block' }}>
      {messages}
    </div>
  );
}
