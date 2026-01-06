


export function ContractHistory({ userId, userName, onClose }: { userId: string, userName?: string, onClose: () => void }) {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="bg-white p-6 rounded-lg shadow-xl">
                <h2 className="text-xl font-bold mb-4">Contract History for {userName}</h2>
                <p>User ID: {userId}</p>
                <button
                    onClick={onClose}
                    className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                    Chiudi
                </button>
            </div>
        </div>
    );
}
