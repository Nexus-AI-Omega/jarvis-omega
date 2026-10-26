package de.jarvisomega.jarvisomegaguard;

import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.Location;
import org.bukkit.World;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabCompleter;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Item;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.player.AsyncPlayerChatEvent;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerMoveEvent;
import org.bukkit.plugin.java.JavaPlugin;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * JarvisOmegaGuardPlugin — Vollautomatisch generiert von J.A.R.V.I.S. OMEGA
 * Umsetzung der Idee: Anti-Cheat & RAM
 */
public final class JarvisOmegaGuardPlugin extends JavaPlugin implements Listener, CommandExecutor, TabCompleter {

    private final Map<UUID, Integer> violationScores = new ConcurrentHashMap<>();
    private String prefix = ChatColor.DARK_GRAY + "[" + ChatColor.AQUA + "J.A.R.V.I.S." + ChatColor.DARK_GRAY + "] " + ChatColor.GRAY;

    @Override
    public void onEnable() {
        saveDefaultConfig();
        Bukkit.getPluginManager().registerEvents(this, this);
        if (getCommand("jarvisomegaguard") != null) {
            getCommand("jarvisomegaguard").setExecutor(this);
            getCommand("jarvisomegaguard").setTabCompleter(this);
        }

        // Autonomer 15-Minuten RAM & Entity-Hygiene Task
        Bukkit.getScheduler().runTaskTimer(this, this::runAutonomousMaintenance, 20L * 60 * 15, 20L * 60 * 15);
        getLogger().info("JarvisOmegaGuard v1.0.0-OMEGA aktiviert! Idee aktiv: Anti-Cheat & RAM");
    }

    private void runAutonomousMaintenance() {
        int removedItems = 0;
        for (World world : Bukkit.getWorlds()) {
            for (Entity entity : world.getEntities()) {
                if (entity instanceof Item && entity.getTicksLived() > 20 * 180) {
                    entity.remove();
                    removedItems++;
                }
            }
        }
        long maxMb = Runtime.getRuntime().maxMemory() / (1024 * 1024);
        long usedMb = (Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory()) / (1024 * 1024);
        getLogger().info("[JARVIS Auto-Wartung] " + removedItems + " alte Boden-Items entfernt. RAM: " + usedMb + "MB / " + maxMb + "MB");
    }

    @EventHandler(priority = EventPriority.LOWEST, ignoreCancelled = true)
    public void onChatSecurity(AsyncPlayerChatEvent event) {
        String msg = event.getMessage();
        if (msg.toLowerCase().contains("${jndi:") || msg.toLowerCase().contains("${lower:")) {
            event.setCancelled(true);
            Player p = event.getPlayer();
            Bukkit.getScheduler().runTask(this, () ->
                p.kickPlayer(ChatColor.RED + "[J.A.R.V.I.S. Cyber-Shield] Exploit-Payload blockiert!")
            );
            getLogger().warning("[SECURITY] Exploit-Versuch im Chat blockiert von: " + p.getName());
        }
    }

    @EventHandler(ignoreCancelled = true)
    public void onMoveCheck(PlayerMoveEvent event) {
        Player p = event.getPlayer();
        if (p.isOp() || p.getAllowFlight() || p.isInsideVehicle() || p.isGliding()) return;
        Location from = event.getFrom();
        Location to = event.getTo();
        if (to == null) return;
        double dx = to.getX() - from.getX();
        double dz = to.getZ() - from.getZ();
        double horizDist = Math.sqrt(dx * dx + dz * dz);
        double maxSpeed = getConfig().getDouble("anti-hacker.max-speed-delta", 1.65);

        if (horizDist > maxSpeed) {
            int score = violationScores.merge(p.getUniqueId(), 1, Integer::sum);
            if (score >= 8) {
                event.setTo(from);
                p.sendMessage(prefix + ChatColor.RED + "Ungewöhnliche Bewegungsgeschwindigkeit erkannt (Anti-Cheat Schutz).");
            }
        }
    }

    @EventHandler
    public void onPlayerJoin(PlayerJoinEvent event) {
        Player p = event.getPlayer();
        p.sendMessage(prefix + ChatColor.GREEN + "Willkommen! Server wird geschützt durch " + ChatColor.AQUA + "JarvisOmegaGuard" + ChatColor.GREEN + ".");
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        String sub = args.length > 0 ? args[0].toLowerCase() : "status";
        Runtime rt = Runtime.getRuntime();
        long usedMb = (rt.totalMemory() - rt.freeMemory()) / (1024 * 1024);
        long maxMb = rt.maxMemory() / (1024 * 1024);

        switch (sub) {
            case "ram":
            case "heal":
                if (!sender.hasPermission("jarvisomegaguard.admin")) {
                    sender.sendMessage(prefix + ChatColor.RED + "Keine Berechtigung.");
                    return true;
                }
                runAutonomousMaintenance();
                sender.sendMessage(prefix + ChatColor.GREEN + "Wartung & Entity-Bereinigung ausgeführt! Aktueller Heap: "
                        + ChatColor.AQUA + usedMb + " MB / " + maxMb + " MB");
                return true;

            case "idea":
                sender.sendMessage(prefix + ChatColor.GOLD + "Aktive Idee: " + ChatColor.WHITE + getConfig().getString("custom-idea.description"));
                if (sender instanceof Player) {
                    Player p = (Player) sender;
                    int xp = getConfig().getInt("custom-idea.reward-xp", 50);
                    p.giveExp(xp);
                    p.sendMessage(prefix + ChatColor.AQUA + "Du hast +" + xp + " Bonus-XP erhalten!");
                }
                return true;

            case "support":
                sender.sendMessage(prefix + ChatColor.YELLOW + "Support-Ticket-Hilfe: Nutze /verlinken im Discord oder öffne das Spieler-Dashboard!");
                return true;

            default:
                sender.sendMessage(prefix + ChatColor.AQUA + "JarvisOmegaGuard Status: " + ChatColor.GREEN + "ONLINE");
                sender.sendMessage(prefix + ChatColor.GRAY + "RAM: " + usedMb + "MB / " + maxMb + "MB | Aktive Spieler: " + Bukkit.getOnlinePlayers().size());
                sender.sendMessage(prefix + ChatColor.GRAY + "Befehle: /jarvisomegaguard <status|heal|ram|idea|support>");
                return true;
        }
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String alias, String[] args) {
        if (args.length == 1) {
            return Arrays.asList("status", "heal", "ram", "idea", "support");
        }
        return Collections.emptyList();
    }
}
