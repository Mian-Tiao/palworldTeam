// Palworld 資料抽取工具(唯讀):掛載遊戲 .pak,列出/匯出 DataTable 為 JSON。
// 用法:
//   dotnet run -- list <關鍵字>
//   dotnet run -- export <輸出資料夾> <套件路徑1> [套件路徑2 ...]
using System.Text;
using CUE4Parse.Compression;
using CUE4Parse.Encryption.Aes;
using CUE4Parse.FileProvider;
using CUE4Parse.MappingsProvider.Usmap;
using CUE4Parse.UE4.Objects.Core.Misc;
using CUE4Parse.UE4.Versions;
using Newtonsoft.Json;

Console.OutputEncoding = Encoding.UTF8;

const string PaksDir = @"C:\Program Files (x86)\Steam\steamapps\common\Palworld\Pal\Content\Paks";
var usmapPath = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "Mappings.usmap");

// Oodle 解壓縮原生庫(CUE4Parse 官方下載器;無參數時自動下載並初始化)
OodleHelper.Initialize();

var provider = new DefaultFileProvider(
    PaksDir, SearchOption.TopDirectoryOnly, false,
    new VersionContainer(EGame.GAME_UE5_1));
provider.MappingsContainer = new FileUsmapTypeMappingsProvider(Path.GetFullPath(usmapPath));
provider.Initialize();
provider.SubmitKey(new FGuid(), new FAesKey(new byte[32])); // 未加密,空金鑰觸發掛載

Console.Error.WriteLine($"已掛載檔案數:{provider.Files.Count}");

var mode = args.Length > 0 ? args[0] : "list";
if (mode == "list")
{
    var keyword = args.Length > 1 ? args[1] : "DataTable";
    foreach (var key in provider.Files.Keys
                 .Where(k => k.Contains(keyword, StringComparison.OrdinalIgnoreCase))
                 .OrderBy(k => k))
        Console.WriteLine(key);
}
else if (mode == "export")
{
    var outDir = args[1];
    Directory.CreateDirectory(outDir);
    foreach (var pkgPath in args.Skip(2))
    {
        try
        {
            var package = provider.LoadPackage(pkgPath);
            var exports = package.GetExports().ToArray();
            var json = JsonConvert.SerializeObject(exports, Formatting.Indented);
            var outFile = Path.Combine(outDir, Path.GetFileNameWithoutExtension(pkgPath) + ".json");
            File.WriteAllText(outFile, json, new UTF8Encoding(false));
            Console.WriteLine($"OK  {pkgPath} → {outFile}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"FAIL {pkgPath}: {ex.Message}");
        }
    }
}
