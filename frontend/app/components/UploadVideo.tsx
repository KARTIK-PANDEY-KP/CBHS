'use client'

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Moon } from "lucide-react";
import { useEffect, useState } from "react";
import JSZip from "jszip";

export default function UploadVideo() {
    const [uploadStatus, setUploadStatus] = useState('');
    const [loading, setIsLoading] = useState(false);
    const [videos, setVideos] = useState<string[]>([]); // Store URLs of videos
    const [selectedVideos, setSelectedVideos] = useState<string[]>([]); // Store selected videos
    const [finalVideo, setFinalVideo] = useState<string | null>(null); // Store final video URL
    useEffect(() => {
        console.log(selectedVideos);
    }, [selectedVideos])
    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
            setIsLoading(true);
            const response = await fetch(`http://127.0.0.1:5000/upload`, {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                const blob = await response.blob();
                const zip = await JSZip.loadAsync(blob);

                // Iterate over each file in the zip and create URLs for the video files
                const videoFiles: any = [];
                zip.forEach((relativePath, file) => {
                    if (file.name.endsWith('.mp4')) { // Ensure it's a video file
                        videoFiles.push(file.async("blob").then(blobData => {
                            return URL.createObjectURL(blobData);
                        }));
                    }
                });

                // Wait for all videos to be processed
                const videoUrls = await Promise.all(videoFiles);
                setVideos(videoUrls);
                setUploadStatus('File uploaded and videos displayed successfully!');
            } else {
                const errorData = await response.json();
                setUploadStatus(`Upload failed: ${errorData.error}`);
            }
        } catch (error) {
            console.error('Error:', error);
            setUploadStatus('An error occurred during upload.');
        }

        setIsLoading(false);
    };

    const handleVideoSelect = (videoUrl: string) => {
        setSelectedVideos((prev) => {
            if (prev.includes(videoUrl)) {
                return prev.filter((url) => url !== videoUrl);
            } else {
                return [...prev, videoUrl];
            }
        });
    };

    // Helper function to log FormData entries


    /*************  ✨ Codeium Command ⭐  *************/
    /**
     * Handle the stitching of videos with AI commentary.
     *
     * Fetches each selected video blob, appends it to a FormData object, and sends
     * a POST request to the server at `http://127.0.0.1:5000/ai-commentary`. If the
     * response is successful, it creates a link to download the resulting video file,
     * and sets the `finalVideo` state to the URL of the resulting video.
     *
     * If the request fails, it sets the `uploadStatus` state to an error message.
     */
    /******  971449e6-bea5-418b-b697-ca23c78fc91e  *******/
    const handleStitchVideos = async () => {
        if (selectedVideos.length === 0) {
            setUploadStatus('Please select videos to stitch.');
            return;
        }

        const formData = new FormData();

        try {
            setIsLoading(true);

            // Fetch all selected video blobs
            const videoBlobs = await Promise.all(selectedVideos.map(async (videoUrl) => {
                const response = await fetch(videoUrl);
                return response.blob();
            }));

            // Append each video blob to FormData (with unique names)
            videoBlobs.forEach((blob, idx) => {
                formData.append('videos', blob, `video_part_${idx}.mp4`);
            });

            const response = await fetch(`http://127.0.0.1:5000/ai-commentary`, {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                const blob = await response.blob();
                const videoUrl = URL.createObjectURL(blob);
                setFinalVideo(videoUrl);

                // Create a link to download the video file
                const link = document.createElement('a');
                link.href = videoUrl;
                link.download = 'stitched_video_with_commentary.mp4';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

                setUploadStatus('Videos successfully stitched and AI commentary applied!');
            } else {
                const errorData = await response.json();
                setUploadStatus(`Stitching failed: ${errorData.error}`);
            }
        } catch (error) {
            console.error('Error:', error);
            setUploadStatus('An error occurred while stitching videos.');
        }

        setIsLoading(false);
    };




    return (
        <div className="flex flex-col min-h-screen bg-black text-white">
            <header className="flex items-center justify-between p-6">
                <div className="flex items-center space-x-4">
                    <svg
                        className=" h-6 w-6 text-white"
                        fill="none"
                        height="24"
                        stroke="currentColor"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        viewBox="0 0 24 24"
                        width="24"
                        xmlns="http://www.w3.org/2000/svg"
                    >
                        <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
                        <line x1="4" x2="4" y1="22" y2="15" />
                    </svg>
                    <span className="text-xl font-bold">Startup</span>
                </div>
                <nav className="hidden md:flex space-x-4">
                    <a className="hover:text-gray-300" href="#">
                        Features
                    </a>
                    <a className="hover:text-gray-300" href="#">
                        Pricing
                    </a>
                    <a className="hover:text-gray-300" href="#">
                        Contact
                    </a>
                </nav>
                <div className="flex items-center space-x-4">
                    <Button className="hidden md:inline-flex" variant="ghost">
                        Login
                    </Button>
                    <Button size="icon" variant="ghost">
                        <Moon className="h-4 w-4" />
                    </Button>
                </div>
            </header>
            <main className="flex-grow flex items-center justify-center px-6 py-12">
                <div className="text-center space-y-8 max-w-3xl">
                    <h1 className="text-5xl md:text-7xl font-bold leading-tight">
                        Get your best MMA highlights
                    </h1>
                    <p className="text-xl md:text-2xl text-gray-400">
                        Upload your video to get started
                    </p>
                    <div className="flex flex-col items-center justify-center space-y-4">
                        <Label htmlFor="file-upload" className="cursor-pointer">
                            <div className="bg-white text-black px-6 py-3 rounded-lg font-semibold hover:bg-gray-200 transition-colors">
                                {loading ? 'Uploading...' : 'Upload Video'}
                            </div>
                            <Input
                                id="file-upload"
                                type="file"
                                accept=".mp4"
                                className="hidden"
                                onChange={handleFileUpload}
                            />
                        </Label>
                        {uploadStatus && (
                            <p className={uploadStatus.includes('successfully') ? 'text-green-500' : 'text-red-500'}>
                                {uploadStatus}
                            </p>
                        )}

                        {videos.length > 0 && (
                            <div className="mt-8 space-y-4">
                                <h2 className="text-2xl font-bold">Extracted Videos:</h2>
                                {videos.map((video, index) => (
                                    <div key={index} className="flex items-center space-x-4">
                                        <input
                                            type="checkbox"
                                            checked={selectedVideos.includes(video)}
                                            onChange={() => handleVideoSelect(video)}
                                        />
                                        <video controls className="w-full max-w-lg" >
                                            <source src={video} type="video/mp4" />
                                            Your browser does not support the video tag.
                                        </video>
                                    </div>
                                ))}
                                <Button
                                    onClick={handleStitchVideos}
                                    className=" bg-white text-black px-6 py-3 rounded-lg font-semibold hover:bg-gray-200 "
                                >
                                    Stitch and Send for AI Commentary
                                </Button>
                            </div>
                        )}

                        {finalVideo && (
                            <div className="mt-8">
                                <h2 className="text-2xl font-bold">Final Video with AI Commentary:</h2>
                                <video controls className="w-full max-w-lg mt-4">
                                    <source src={finalVideo} type="video/mp4" />
                                    Your browser does not support the video tag.
                                </video>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
