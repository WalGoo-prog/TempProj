using System;
using System.IO;
using UnityEngine;

public static class WavUtility
{
    public static byte[] FromAudioClip(AudioClip clip)
    {
        using (var stream = new MemoryStream())
        {
            var writer = new BinaryWriter(stream);
            var samples = new float[clip.samples * clip.channels];
            clip.GetData(samples, 0);

            Int16[] intData = new Int16[samples.Length];
            Byte[] bytesData = new Byte[samples.Length * 2];
            int rescaleFactor = 32767;

            for (int i = 0; i < samples.Length; i++)
            {
                intData[i] = (short)(samples[i] * rescaleFactor);
                byte[] byteArr = BitConverter.GetBytes(intData[i]);
                byteArr.CopyTo(bytesData, i * 2);
            }

            WriteHeader(writer, clip);
            writer.Write(bytesData);
            return stream.ToArray();
        }
    }

    private static void WriteHeader(BinaryWriter writer, AudioClip clip)
    {
        var hz = clip.frequency;
        var channels = clip.channels;
        var samples = clip.samples;

        writer.Write(new char[4] { 'R', 'I', 'F', 'F' });
        writer.Write(36 + samples * channels * 2);
        writer.Write(new char[4] { 'W', 'A', 'V', 'E' });
        writer.Write(new char[4] { 'f', 'm', 't', ' ' });
        writer.Write(16);
        writer.Write((ushort)1);
        writer.Write((ushort)channels);
        writer.Write(hz);
        writer.Write(hz * channels * 2);
        writer.Write((ushort)(channels * 2));
        writer.Write((ushort)16);
        writer.Write(new char[4] { 'd', 'a', 't', 'a' });
        writer.Write(samples * channels * 2);
    }
}