#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_project.py

Ce script genere l'integralite du projet Maven "CustomItems" (plugin Spigot 1.8.x)
dans le dossier courant, sous CustomItems/...

Pourquoi un script et pas directement les fichiers ?
Le mode Cowork qui a genere ce livrable ne pouvait pas creer d'arborescence
de dossiers directement sur cette machine. Ce script embarque donc tout le
code source et recree la structure exacte du projet quand vous l'executez :

    python3 build_project.py

Ensuite, pour compiler :
    cd CustomItems
    mvn clean package
(necessite d'avoir installe spigot-api 1.8.8 dans votre repo local Maven via BuildTools.jar)

Le jar compile se trouvera dans CustomItems/target/CustomItems.jar
"""
import os

FILES = {}

def add(path, content):
    FILES[path] = content

add("pom.xml", """<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>fr.faction</groupId>
    <artifactId>CustomItems</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <name>CustomItems</name>
    <description>Systeme de custom items premium (tier Emeraude) pour serveur PvP Faction Spigot 1.8.x</description>

    <properties>
        <maven.compiler.source>1.8</maven.compiler.source>
        <maven.compiler.target>1.8</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>

    <repositories>
        <repository>
            <id>spigot-repo</id>
            <url>https://hub.spigotmc.org/nexus/content/repositories/snapshots/</url>
        </repository>
    </repositories>

    <dependencies>
        <!--
            Spigot API 1.8.8 (NMS revision v1_8_R3).
            Installer prealablement via BuildTools.jar (argument de revision 1.8.8).
        -->
        <dependency>
            <groupId>org.spigotmc</groupId>
            <artifactId>spigot-api</artifactId>
            <version>1.8.8-R0.1-SNAPSHOT</version>
            <scope>provided</scope>
        </dependency>
    </dependencies>

    <build>
        <finalName>${project.name}</finalName>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <source>8</source>
                    <target>8</target>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
""")

add("src/main/resources/plugin.yml", """name: CustomItems
version: 1.0.0
main: fr.faction.customitems.CustomItemsPlugin
author: Kasey
description: Systeme de custom items tier Emeraude pour serveur PvP Faction 1.8.x
softdepend: [WorldGuard, Factions, FactionsUUID, GriefPrevention]
commands:
  citem:
    description: Commande principale du systeme de custom items
    usage: /<command> give <joueur> <id> [quantite] | list | id
    permission: customitems.admin
    permission-message: "&cVous n'avez pas la permission d'utiliser cette commande."
permissions:
  customitems.admin:
    description: Permet de donner et lister les custom items
    default: op
  customitems.use:
    description: Permet d'utiliser les effets des custom items
    default: true
""")

add("src/main/resources/config.yml", """# ========================================================
# Configuration - CustomItems
# ========================================================

# Rayon de la zone de minage du hammer emeraude (3x3 => valeur 1 de chaque cote)
hammer.emerald.radius: 1
hammer.reinforced.radius: 2

shovel.emerald.radius: 1
shovel.reinforced.radius: 2

hoe.emerald.radius: 0
hoe.reinforced.radius: 1

axe.emerald.length: 3

# Bonus de degats (points de coeur, 1.0 = un demi coeur) ajoutes par rapport a une epee diamant
sword.emerald.bonus-damage: 3.0
sword.reinforced.bonus-damage: 5.0

# Reduction de degats supplementaire (pourcentage, 0.05 = 5%) par piece d'armure equipee
armor.emerald.reduction-per-piece: 0.05
armor.reinforced.reduction-per-piece: 0.08

# Active/desactive la verification des protections (Factions/WorldGuard/etc.) avant destruction de zone
protection.check-enabled: true

# Active les logs de debug dans la console
debug: false
""")
add("src/main/java/fr/faction/customitems/api/CustomItem.java", """package fr.faction.customitems.api;

import org.bukkit.inventory.ItemStack;

/**
 * Contrat de base que doit respecter chaque custom item du systeme.
 * Chaque implementation possede un identifiant interne unique (utilise pour
 * le tag NBT "CustomItemId") et sait construire son propre ItemStack fini
 * (nom, lore, materiau, enchantements vanilla, unbreakable, etc.).
 */
public interface CustomItem {

    /**
     * @return l'identifiant interne unique de l'item (ex: "EMERALD_HAMMER").
     * Utilise comme cle dans le CustomItemRegistry et comme valeur du tag NBT.
     */
    String getId();

    /**
     * @return un nouvel ItemStack pret a l'emploi representant cet item.
     * Doit toujours retourner une NOUVELLE instance (pas de partage d'etat mutable).
     */
    ItemStack build();

    /**
     * @return true si l'item doit etre incassable (NBT Unbreakable + annulation
     * de la perte de durabilite). Par convention, tous les items "renforces"
     * retournent true ici.
     */
    boolean isUnbreakable();
}
""")

add("src/main/java/fr/faction/customitems/api/MiningTool.java", """package fr.faction.customitems.api;

/**
 * Marqueur pour les outils capables de casser une zone de blocs autour du
 * bloc cible (hammer, pelle...). Implementee par les items concernes et
 * consommee par MiningListener.
 */
public interface MiningTool {

    /**
     * @return le rayon de la zone autour du bloc casse (1 = zone 3x3, 2 = zone 5x5).
     */
    int getRadius();

    /**
     * @return true si seuls les blocs du MEME type que le bloc cible doivent
     * etre casses (regle imposee par le cahier des charges pour tous les outils
     * de zone : "Casse uniquement le meme type de bloc").
     */
    default boolean sameBlockTypeOnly() {
        return true;
    }
}
""")

add("src/main/java/fr/faction/customitems/api/ReplantingHoe.java", """package fr.faction.customitems.api;

/**
 * Marqueur pour les houes capables de recolter et replanter automatiquement
 * une zone de cultures. Consommee par FarmingListener.
 */
public interface ReplantingHoe {

    /**
     * @return le rayon de la zone de recolte (0 = uniquement le bloc casse,
     * 1 = zone 3x3 autour du bloc casse).
     */
    int getRadius();
}
""")

add("src/main/java/fr/faction/customitems/api/TreeFeller.java", """package fr.faction.customitems.api;

/**
 * Marqueur pour la hache emeraude renforcee : casser une seule buche coupe
 * l'integralite de l'arbre (tree capitator). Consommee par MiningListener.
 */
public interface TreeFeller {
}
""")

add("src/main/java/fr/faction/customitems/api/WeaponBonus.java", """package fr.faction.customitems.api;

/**
 * Marqueur pour les armes infligeant un bonus de degats par rapport au
 * materiau vanilla equivalent. Necessaire car l'API Bukkit 1.8 ne propose
 * pas encore ItemMeta#addAttributeModifier (introduit en 1.13) : le bonus
 * est donc applique manuellement par CombatListener via EntityDamageByEntityEvent.
 */
public interface WeaponBonus {

    /**
     * @return les degats bonus (en demi-coeurs, ex: 3.0 = 1.5 coeur) ajoutes
     * a l'attaque au corps a corps.
     */
    double getBonusDamage();
}
""")

add("src/main/java/fr/faction/customitems/api/ArmorBonus.java", """package fr.faction.customitems.api;

/**
 * Marqueur pour les pieces d'armure offrant une reduction de degats
 * supplementaire par rapport au diamant. Meme limitation que WeaponBonus :
 * pas d'attribute modifiers natifs en 1.8, le bonus est donc applique
 * manuellement par CombatListener via EntityDamageEvent.
 */
public interface ArmorBonus {

    /**
     * @return le pourcentage de reduction de degats supplementaire apporte
     * par cette piece (ex: 0.05 = 5%).
     */
    double getDamageReductionPercent();
}
""")
add("src/main/java/fr/faction/customitems/nbt/NBTEditor.java", """package fr.faction.customitems.nbt;

import org.bukkit.Bukkit;
import org.bukkit.inventory.ItemStack;

import java.lang.reflect.Method;

/**
 * Utilitaire d'acces au NBT brut d'un ItemStack via reflexion NMS.
 *
 * Pourquoi de la reflexion et pas l'API Bukkit standard ?
 * En Spigot 1.8.x, ItemMeta ne propose ni setUnbreakable() (ajoute en 1.11),
 * ni de PersistentDataContainer (ajoute en 1.14). Pour marquer un item comme
 * incassable (NBT "Unbreakable") ou pour lui attribuer un identifiant interne
 * invisible ("CustomItemId"), il faut donc manipuler le NBTTagCompound NMS
 * directement. Cette classe encapsule toute cette reflexion afin que le
 * reste du plugin n'ait jamais a en dependre directement.
 *
 * Compatible avec toutes les revisions NMS 1.8 (v1_8_R1, v1_8_R2, v1_8_R3)
 * puisque le nom de package est detecte dynamiquement au chargement.
 */
public final class NBTEditor {

    /** Cle NBT utilisee pour stocker l'identifiant interne du custom item. */
    public static final String CUSTOM_ID_KEY = "CustomItemId";

    private static final String VERSION;
    private static boolean available = true;

    static {
        String pkg = Bukkit.getServer().getClass().getPackage().getName();
        VERSION = pkg.substring(pkg.lastIndexOf('.') + 1);
    }

    private NBTEditor() {
    }

    public static boolean isAvailable() {
        return available;
    }

    private static Class<?> nmsClass(String name) throws ClassNotFoundException {
        return Class.forName("net.minecraft.server." + VERSION + "." + name);
    }

    private static Class<?> obcClass(String name) throws ClassNotFoundException {
        return Class.forName("org.bukkit.craftbukkit." + VERSION + "." + name);
    }

    private static Object toNMSCopy(ItemStack item) throws Exception {
        Class<?> craftItemStack = obcClass("inventory.CraftItemStack");
        Method asNMSCopy = craftItemStack.getMethod("asNMSCopy", ItemStack.class);
        return asNMSCopy.invoke(null, item);
    }

    private static ItemStack toBukkitCopy(Object nmsItem) throws Exception {
        Class<?> craftItemStack = obcClass("inventory.CraftItemStack");
        Method asBukkitCopy = craftItemStack.getMethod("asBukkitCopy", nmsClass("ItemStack"));
        return (ItemStack) asBukkitCopy.invoke(null, nmsItem);
    }

    private static Object getOrCreateTag(Object nmsItem) throws Exception {
        Class<?> nmsItemStackClass = nmsClass("ItemStack");
        Method hasTag = nmsItemStackClass.getMethod("hasTag");
        Method getTag = nmsItemStackClass.getMethod("getTag");
        Method setTag = nmsItemStackClass.getMethod("setTag", nmsClass("NBTTagCompound"));

        Object tag;
        if ((boolean) hasTag.invoke(nmsItem)) {
            tag = getTag.invoke(nmsItem);
        } else {
            tag = nmsClass("NBTTagCompound").newInstance();
            setTag.invoke(nmsItem, tag);
        }
        return tag;
    }

    /**
     * Ecrit une paire cle/valeur String dans le NBT racine de l'item et
     * retourne un NOUVEL ItemStack (les ItemStack Bukkit sont immuables du
     * point de vue de cette API : on remplace toujours la reference).
     */
    public static ItemStack setString(ItemStack item, String key, String value) {
        if (!available) return item;
        try {
            Object nmsItem = toNMSCopy(item);
            Object tag = getOrCreateTag(nmsItem);
            tag.getClass().getMethod("setString", String.class, String.class).invoke(tag, key, value);
            return toBukkitCopy(nmsItem);
        } catch (Exception ex) {
            available = false;
            Bukkit.getLogger().warning("[CustomItems] NBTEditor indisponible sur cette version NMS (" + VERSION + "): " + ex);
            return item;
        }
    }

    public static String getString(ItemStack item, String key) {
        if (!available || item == null) return null;
        try {
            Object nmsItem = toNMSCopy(item);
            Class<?> nmsItemStackClass = nmsClass("ItemStack");
            boolean hasTag = (boolean) nmsItemStackClass.getMethod("hasTag").invoke(nmsItem);
            if (!hasTag) return null;
            Object tag = nmsItemStackClass.getMethod("getTag").invoke(nmsItem);
            boolean hasKey = (boolean) tag.getClass().getMethod("hasKey", String.class).invoke(tag, key);
            if (!hasKey) return null;
            return (String) tag.getClass().getMethod("getString", String.class).invoke(tag, key);
        } catch (Exception ex) {
            return null;
        }
    }

    public static ItemStack setBoolean(ItemStack item, String key, boolean value) {
        if (!available) return item;
        try {
            Object nmsItem = toNMSCopy(item);
            Object tag = getOrCreateTag(nmsItem);
            tag.getClass().getMethod("setBoolean", String.class, boolean.class).invoke(tag, key, value);
            return toBukkitCopy(nmsItem);
        } catch (Exception ex) {
            available = false;
            Bukkit.getLogger().warning("[CustomItems] NBTEditor indisponible sur cette version NMS (" + VERSION + "): " + ex);
            return item;
        }
    }

    /** Marque l'item comme incassable au sens NBT vanilla (tag "Unbreakable"). */
    public static ItemStack setUnbreakable(ItemStack item) {
        return setBoolean(item, "Unbreakable", true);
    }

    /** Ecrit l'identifiant interne du custom item dans le NBT (invisible au joueur). */
    public static ItemStack setCustomId(ItemStack item, String id) {
        return setString(item, CUSTOM_ID_KEY, id);
    }

    /** @return l'identifiant interne du custom item, ou null si l'item n'en est pas un. */
    public static String getCustomId(ItemStack item) {
        return getString(item, CUSTOM_ID_KEY);
    }
}
""")
add("src/main/java/fr/faction/customitems/util/ColorUtil.java", """package fr.faction.customitems.util;

import org.bukkit.ChatColor;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public final class ColorUtil {

    private ColorUtil() {
    }

    public static String c(String s) {
        return ChatColor.translateAlternateColorCodes('&', s);
    }

    public static List<String> c(String... lines) {
        List<String> result = new ArrayList<>();
        for (String line : lines) {
            result.add(c(line));
        }
        return result;
    }

    public static List<String> c(List<String> lines) {
        List<String> result = new ArrayList<>(lines.size());
        for (String line : lines) {
            result.add(c(line));
        }
        return result;
    }
}
""")

add("src/main/java/fr/faction/customitems/api/ItemBuilder.java", """package fr.faction.customitems.api;

import fr.faction.customitems.nbt.NBTEditor;
import fr.faction.customitems.util.ColorUtil;
import org.bukkit.Material;
import org.bukkit.enchantments.Enchantment;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;

import java.util.ArrayList;
import java.util.List;

/**
 * Construit les ItemStack des custom items en respectant le format visuel
 * impose par le cahier des charges :
 *
 *   Nom   : &e[ETOILE] &7Nom de l'item en &a/&2 (emeraude / emeraude renforcee)
 *   Lore  : description + ligne de progression + "&aCustom enchants autorises"
 *
 * Regle des items renforces : Unbreakable via NBT (pas de perte de durabilite),
 * appliquee automatiquement si unbreakable(true) est appele.
 */
public class ItemBuilder {

    public static final String STAR = "\\u2B50"; // etoile jaune palissante (Unicode, pas de couleur fixe imposee au glyphe)

    private final Material material;
    private int amount = 1;
    private short durability = 0;
    private String displayName;
    private final List<String> lore = new ArrayList<>();
    private boolean unbreakable = false;
    private String customId;
    private final List<EnchantEntry> enchants = new ArrayList<>();

    private static class EnchantEntry {
        Enchantment enchantment;
        int level;
        EnchantEntry(Enchantment e, int l) { this.enchantment = e; this.level = l; }
    }

    public ItemBuilder(Material material) {
        this.material = material;
    }

    public ItemBuilder amount(int amount) {
        this.amount = amount;
        return this;
    }

    public ItemBuilder durability(short durability) {
        this.durability = durability;
        return this;
    }

    /**
     * Definit le nom affiche a partir du "nom simple" de l'item (ex: "Hammer").
     * Applique automatiquement le format impose :
     *   &e[ETOILE] &7<nom> en &a/&2<tier>
     */
    public ItemBuilder emeraldName(String itemName, boolean reinforced) {
        String tierColor = reinforced ? "&2" : "&a";
        String tierWord = reinforced ? "emeraude renforcee" : "emeraude";
        this.displayName = ColorUtil.c("&e" + STAR + " &7" + itemName + " en " + tierColor + tierWord);
        return this;
    }

    public ItemBuilder rawName(String name) {
        this.displayName = ColorUtil.c(name);
        return this;
    }

    public ItemBuilder loreLine(String line) {
        this.lore.add(ColorUtil.c(line));
        return this;
    }

    public ItemBuilder blankLine() {
        this.lore.add("");
        return this;
    }

    /** Ajoute la ligne de progression standard, ex: "&aEmeraude > &bDiamant". */
    public ItemBuilder progression(boolean reinforced) {
        if (reinforced) {
            loreLine("&2Emeraude renforcee &7> &aEmeraude");
        } else {
            loreLine("&aEmeraude &7> &bDiamant");
        }
        return this;
    }

    public ItemBuilder enchant(Enchantment enchantment, int level) {
        this.enchants.add(new EnchantEntry(enchantment, level));
        return this;
    }

    public ItemBuilder unbreakable(boolean unbreakable) {
        this.unbreakable = unbreakable;
        return this;
    }

    public ItemBuilder customId(String id) {
        this.customId = id;
        return this;
    }

    public ItemStack build() {
        ItemStack item = new ItemStack(material, amount);
        if (durability != 0) {
            item.setDurability(durability);
        }

        ItemMeta meta = item.getItemMeta();
        if (displayName != null) {
            meta.setDisplayName(displayName);
        }

        // Ligne finale obligatoire imposee par le cahier des charges
        List<String> finalLore = new ArrayList<>(lore);
        finalLore.add(ColorUtil.c("&aCustom enchants autorises"));
        meta.setLore(finalLore);

        for (EnchantEntry entry : enchants) {
            meta.addEnchant(entry.enchantment, entry.level, true);
        }

        item.setItemMeta(meta);

        if (unbreakable) {
            item = NBTEditor.setUnbreakable(item);
        }
        if (customId != null) {
            item = NBTEditor.setCustomId(item, customId);
        }

        return item;
    }
}
""")
add("src/main/java/fr/faction/customitems/api/ExtraDurability.java", """package fr.faction.customitems.api;

/**
 * Marqueur pour les items "de base" (non renforces) qui doivent avoir plus
 * de durabilite qu'un equivalent diamant, sans etre totalement incassables.
 *
 * Limitation technique : Bukkit 1.8 ne permet pas de modifier la durabilite
 * maximale d'un Material (c'est code en dur cote NMS). On simule donc une
 * durabilite superieure en annulant probabilistiquement une partie des
 * degats de durabilite : avec un multiplicateur de 1.5, l'item perd en
 * moyenne un point de durabilite toutes les 1.5 utilisations au lieu de
 * chaque utilisation, soit +50% de duree de vie effective.
 * Consommee par ItemDurabilityListener.
 */
public interface ExtraDurability {

    /**
     * @return le multiplicateur de duree de vie effective (1.5 = +50%).
     */
    double getDurabilityMultiplier();
}
""")
add("src/main/java/fr/faction/customitems/items/tools/EmeraldHammer.java", """package fr.faction.customitems.items.tools;

import fr.faction.customitems.api.CustomItem;
import fr.faction.customitems.api.ExtraDurability;
import fr.faction.customitems.api.ItemBuilder;
import fr.faction.customitems.api.MiningTool;
import org.bukkit.Material;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.inventory.ItemStack;

public class EmeraldHammer implements CustomItem, MiningTool, ExtraDurability {

    public static final String ID = "EMERALD_HAMMER";
    private final int radius;

    public EmeraldHammer(FileConfiguration config) {
        this.radius = config.getInt("hammer.emerald.radius", 1);
    }

    @Override
    public String getId() {
        return ID;
    }

    @Override
    public int getRadius() {
        return radius;
    }

    @Override
    public boolean isUnbreakable() {
        return false;
    }

    @Override
    public double getDurabilityMultiplier() {
        return 1.5;
    }

    @Override
    public ItemStack build() {
        return new ItemBuilder(Material.DIAMOND_PICKAXE)
                .emeraldName("Hammer", false)
                .loreLine("&7Permet de casser les blocs en zone 3x3.")
                .loreLine("&7Ne casse que le meme type de bloc que celui vise.")
                .loreLine("&7Respecte les claims et protections du serveur.")
                .blankLine()
                .progression(false)
                .customId(ID)
                .build();
    }
}
""")

add("src/main/java/fr/faction/customitems/items/tools/ReinforcedEmeraldHammer.java", """package fr.faction.customitems.items.tools;

import fr.faction.customitems.api.CustomItem;
import fr.faction.customitems.api.ItemBuilder;
import fr.faction.customitems.api.MiningTool;
import org.bukkit.Material;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.inventory.ItemStack;

public class ReinforcedEmeraldHammer implements CustomItem, MiningTool {

    public static final String ID = "REINFORCED_EMERALD_HAMMER";
    private final int radius;

    public ReinforcedEmeraldHammer(FileConfiguration config) {
        this.radius = config.getInt("hammer.reinforced.radius", 2);
    }

    @Override
    public String getId() {
        return ID;
    }

    @Override
    public int getRadius() {
        return radius;
    }

    @Override
    public boolean isUnbreakable() {
        return true;
    }

    @Override
    public ItemStack build() {
        return new ItemBuilder(Material.DIAMOND_PICKAXE)
                .emeraldName("Hammer", true)
                .loreLine("&7Permet de casser les blocs en zone 5x5.")
                .loreLine("&7Plus rapide que le Hammer emeraude.")
                .loreLine("&7Ne casse que le meme type de bloc que celui vise.")
                .loreLine("&7Respecte les claims et protections du serveur.")
                .blankLine()
                .progression(true)
                .unbreakable(true)
                .customId(ID)
                .build();
    }
}
""")
add("src/main/java/fr/faction/customitems/items/tools/EmeraldHoe.java", """package fr.faction.customitems.items.tools;

import fr.faction.customitems.api.CustomItem;
import fr.faction.customitems.api.ExtraDurability;
import fr.faction.customitems.api.ItemBuilder;
import fr.faction.customitems.api.ReplantingHoe;
import org.bukkit.Material;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.inventory.ItemStack;

public class EmeraldHoe implements CustomItem, ReplantingHoe, ExtraDurability {

    public static final String ID = "EMERALD_HOE";
    private final int radius;

    public EmeraldHoe(FileConfiguration config) {
        this.radius = config.getInt("hoe.emerald.radius", 0);
    }

    @Override
    public String getId() {
        return ID;
    }

    @Override
    public int getRadius() {
        return radius;
    }

    @Override
    public boolean isUnbreakable() {
        return false;
    }

    @Override
    public double getDurabilityMultiplier() {
        return 1.5;
    }

    @Override
    public ItemStack build() {
        return new ItemBuilder(Material.DIAMOND_HOE)
                .emeraldName("Houe", false)
                .loreLine("&7Casse et replante automatiquement les plantations.")
                .loreLine("&7Necessite d'avoir les graines correspondantes.")
                .loreLine("&7Compatible : ble, carottes, pommes de terre, betteraves.")
                .blankLine()
                .progression(false)
                .customId(ID)
                .build();
    }
}
""")

add("src/main/java/fr/faction/customitems/items/tools/ReinforcedEmeraldHoe.java", """package fr.faction.customitems.items.tools;

import fr.faction.customitems.api.CustomItem;
import fr.faction.customitems.api.ItemBuilder;
import fr.faction.customitems.api.ReplantingHoe;
import org.bukkit.Material;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.inventory.ItemStack;

public class ReinforcedEmeraldHoe implements CustomItem, ReplantingHoe {

    public static final String ID = "REINFORCED_EMERALD_HOE";
    private final int radius;

    public ReinforcedEmeraldHoe(FileConfiguration config) {
        this.radius = config.getInt("hoe.reinforced.radius", 1);
    }

    @Override
    public String getId() {
        return ID;
    }

    @Override
    public int getRadius() {
        return radius;
    }

    @Override
    public boolean isUnbreakable() {
        return true;
    }

    @Override
    public ItemStack build() {
        return new ItemBuilder(Material.DIAMOND_HOE)
                .emeraldName("Houe", true)
                .loreLine("&7Recolte une zone 3x3 de plantations.")
                .loreLine("&7Replante automatiquement chaque emplacement.")
                .loreLine("&7Necessite d'avoir les graines correspondantes.")
                .blankLine()
                .progression(true)
                .unbreakable(true)
                .customId(ID)
                .build();
    }
}
""")
add("src/main/java/fr/faction/customitems/items/tools/EmeraldPickaxe.java", """package fr.faction.customitems.items.tools;

import fr.faction.customitems.api.CustomItem;
import fr.faction.customitems.api.ExtraDurability;
import fr.faction.customitems.api.ItemBuilder;
import org.bukkit.Material;
import org.bukkit.enchantments.Enchantment;
import org.bukkit.inventory.ItemStack;

/**
 * Pioche emeraude : plus rapide qu'une pioche diamant (Efficacite I offerte
 * de base, cumulable ensuite normalement via table d'enchantement/enclume
 * jusqu'au niveau V vanilla) et plus grande duree de vie effective.
 */
public class EmeraldPickaxe implements CustomItem, ExtraDurability {

    public static final String ID = "EMERALD_PICKAXE";

    @Override
    public String getId() {
        return ID;
    }

    @Override
    public boolean isUnbreakable() {
        return false;
    }

    @Override
    public double getDurabilityMultiplier() {
        return 1.5;
    }

    @Override
    public ItemStack build() {
        return new ItemBuilder(Material.DIAMOND_PICKAXE)
                .emeraldName("Pioche", false)
                .loreLine("&7Plus rapide qu'une pioche en diamant.")
                .loreLine("&7Plus grande duree de vie qu'une pioche en diamant.")
                .blankLine()
                .progression(false)
                .enchant(Enchantment.DIG_SPEED, 1)
                .customId(ID)
                .build();
    }
}
""")

add("src/main/java/fr/faction/customitems/items/tools/ReinforcedEmeraldPickaxe.java", """package fr.faction.customitems.items.tools;

import fr.faction.customitems.api.CustomItem;
import fr.faction.customitems.api.ItemBuilder;
import org.bukkit.Material;
import org.bukkit.enchantments.Enchantment;
import org.bukkit.inventory.ItemStack;

/**
 * Pioche emeraude renforcee : Efficacite II offerte de base (superieure a la
 * pioche emeraude simple), Unbreakable.
 *
 * Note sur les paliers annonces dans le cahier des charges (Obsidienne
 * ~2s avec Efficacite V, Packed Ice / Mossy Cobblestone one-shot avec
 * Efficacite V + Haste II) : ce sont les temps de minage vanilla reels
 * obtenus des lors que le joueur combine cette pioche (compatible avec les
 * enchantements vanilla jusqu'a Efficacite V) avec l'effet de potion Haste II.
 * Aucune surcouche n'est necessaire : la pioche etant compatible avec tous
 * les enchantements vanilla et deja plus rapide qu'une pioche diamant de
 * base, ces paliers sont atteints naturellement par le moteur de Minecraft.
 */
public class ReinforcedEmeraldPickaxe implements CustomItem {

    public static final String ID = "REINFORCED_EMERALD_PICKAXE";

    @Override
    public String getId() {
        return ID;
    }

    @Override
    public boolean isUnbreakable() {
        return true;
    }

    @Override
    public ItemStack build() {
        return new ItemBuilder(Material.DIAMOND_PICKAXE)
                .emeraldName("Pioche", true)
                .loreLine("&7Plus rapide que la pioche emeraude.")
                .loreLine("&7Incassable.")
                .blankLine()
                .loreLine("&7Obsidienne (Efficacite V) : &f~2 secondes")
                .loreLine("&7Packed Ice (Eff. V + Haste II) : &fOne shot")
                .loreLine("&7Mossy Cobblestone (Eff. V + Haste II) : &fOne shot")
                .blankLine()
                .progression(true)
                .enchant(Enchantment.DIG_SPEED, 2)
                .unbreakable(true)
                .customId(ID)
                .build();
    }
}
""")

add("src/main/java/fr/faction/customitems/items/tools/EmeraldShovel.java", """package fr.faction.customitems.items.tools;

import fr.faction.customitems.api.CustomItem;
import fr.faction.customitems.api.ExtraDurability;
import fr.faction.customitems.api.ItemBuilder;
import fr.faction.customitems.api.MiningTool;
import org.bukkit.Material;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.inventory.ItemStack;

public class EmeraldShovel implements CustomItem, MiningTool, ExtraDurability {

    public static final String ID = "EMERALD_SHOVEL";
    private final int radius;

    public EmeraldShovel(FileConfiguration config) {
        this.radius = config.getInt("shovel.emerald.radius", 1);
    }

    @Override
    public String getId() {
        return ID;
    }

    @Override
    public int getRadius() {
        return radius;
    }

    @Override
    public boolean isUnbreakable() {
        return false;
    }

    @Override
    public double getDurabilityMultiplier() {
        return 1.5;
    }

    @Override
    public ItemStack build() {
        return new ItemBuilder(Material.DIAMOND_SPADE)
                .emeraldName("Pelle", false)
                .loreLine("&7Casse en zone 3x3 : terre, sable, gravier, argile.")
                .loreLine("&7Ne casse que le meme type de bloc que celui vise.")
                .blankLine()
                .progression(false)
                .customId(ID)
                .build();
    }
}
""")

add("src/main/java/fr/faction/customitems/items/tools/ReinforcedEmeraldShovel.java", """package fr.faction.customitems.items.tools;

import fr.faction.customitems.api.CustomItem;
import fr.faction.customitems.api.ItemBuilder;
import fr.faction.customitems.api.MiningTool;
import org.bukkit.Material;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.inventory.ItemStack;

public class ReinforcedEmeraldShovel implements CustomItem, MiningTool {

    public static final String ID = "REINFORCED_EMERALD_SHOVEL";
    private final int radius;

    public ReinforcedEmeraldShovel(FileConfiguration config) {
        this.radius = config.getInt("shovel.reinforced.radius", 2);
    }

    @Override
    public String getId() {
        return ID;
    }

    @Override
    public int getRadius() {
        return radius;
    }

    @Override
    public boolean isUnbreakable() {
        return true;
    }

    @Override
    public ItemStack build() {
        return new ItemBuilder(Material.DIAMOND_SPADE)
                .emeraldName("Pelle", true)
                .loreLine("&7Casse en zone 5x5 : terre, sable, gravier, argile.")
                .loreLine("&7Incassable.")
                .blankLine()
                .progression(true)
                .unbreakable(true)
                .customId(ID)
                .build();
    }
}
""")

add("src/main/java/fr/faction/customitems/items/tools/EmeraldAxe.java", """package fr.faction.customitems.items.tools;

import fr.faction.customitems.api.CustomItem;
import fr.faction.customitems.api.ExtraDurability;
import fr.faction.customitems.api.ItemBuilder;
import fr.faction.customitems.api.MiningTool;
import org.bukkit.Material;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.inventory.ItemStack;

/**
 * La hache emeraude casse le bois en colonne 1x3 (le bloc vise + les 2
 * au-dessus dans l'axe vertical de la buche), utile pour degager rapidement
 * un tronc sans abattre tout l'arbre (reserve a la version renforcee).
 */
public class EmeraldAxe implements CustomItem, MiningTool, ExtraDurability {

    public static final String ID = "EMERALD_AXE";
    private final int columnLength;

    public EmeraldAxe(FileConfiguration config) {
        this.columnLength = config.getInt("axe.emerald.length", 3);
    }

    @Override
    public String getId() {
        return ID;
    }

    @Override
    public int getRadius() {
        return columnLength;
    }

    @Override
    public boolean isUnbreakable() {
        return false;
    }

    @Override
    public double getDurabilityMultiplier() {
        return 1.5;
    }

    @Override
    public ItemStack build() {
        return new ItemBuilder(Material.DIAMOND_AXE)
                .emeraldName("Hache", false)
                .loreLine("&7Casse le bois en colonne (1x3).")
                .loreLine("&7Compatible avec tous les types de buches.")
                .blankLine()
                .progression(false)
                .customId(ID)
                .build();
    }
}
""")

add("src/main/java/fr/faction/customitems/items/tools/ReinforcedEmeraldAxe.java", """package fr.faction.customitems.items.tools;

import fr.faction.customitems.api.CustomItem;
import fr.faction.customitems.api.ItemBuilder;
import fr.faction.customitems.api.TreeFeller;
import org.bukkit.Material;
import org.bukkit.inventory.ItemStack;

/**
 * Hache emeraude renforcee : "tree capitator". Casser une seule buche coupe
 * l'integralite de l'arbre (toutes les buches connectees), voir MiningListener.
 */
public class ReinforcedEmeraldAxe implements CustomItem, TreeFeller {

    public static final String ID = "REINFORCED_EMERALD_AXE";

    @Override
    public String getId() {
        return ID;
    }

    @Override
    public boolean isUnbreakable() {
        return true;
    }

    @Override
    public ItemStack build() {
        return new ItemBuilder(Material.DIAMOND_AXE)
                .emeraldName("Hache", true)
                .loreLine("&7Tree Capitator : coupe l'arbre entier en un coup.")
                .loreLine("&7Plus rapide. Incassable.")
                .blankLine()
                .progression(true)
                .unbreakable(true)
                .customId(ID)
                .build();
    }
}
""")
add("src/main/java/fr/faction/customitems/items/armor/EmeraldArmorItem.java", """package fr.faction.customitems.items.armor;

import fr.faction.customitems.api.ArmorBonus;
import fr.faction.customitems.api.CustomItem;
import fr.faction.customitems.api.ExtraDurability;
import fr.faction.customitems.api.ItemBuilder;
import org.bukkit.Material;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.inventory.ItemStack;

/**
 * Classe generique pour les 4 pieces d'armure emeraude (et leurs variantes
 * renforcees). Le materiau de base reste DIAMOND_* : cela garantit des
 * points d'armure vanilla deja superieurs a toute autre armure, la
 * progression "superieure au diamant" etant ensuite assuree par le bonus
 * de reduction de degats supplementaire (ArmorBonus, applique par
 * CombatListener) - l'API Bukkit 1.8 ne proposant pas d'attribute modifiers
 * natifs (ajoutes en 1.13) pour creer un materiau d'armure totalement inedit.
 */
public class EmeraldArmorItem implements CustomItem, ArmorBonus, ExtraDurability {

    public enum Slot {
        HELMET("Casque", Material.DIAMOND_HELMET),
        CHESTPLATE("Plastron", Material.DIAMOND_CHESTPLATE),
        LEGGINGS("Jambieres", Material.DIAMOND_LEGGINGS),
        BOOTS("Bottes", Material.DIAMOND_BOOTS);

        final String displayName;
        final Material material;

        Slot(String displayName, Material material) {
            this.displayName = displayName;
            this.material = material;
        }
    }

    private final Slot slot;
    private final boolean reinforced;
    private final double reductionPercent;
    private final String id;

    public EmeraldArmorItem(Slot slot, boolean reinforced, FileConfiguration config) {
        this.slot = slot;
        this.reinforced = reinforced;
        this.id = (reinforced ? "REINFORCED_EMERALD_" : "EMERALD_") + slot.name();
        this.reductionPercent = reinforced
                ? config.getDouble("armor.reinforced.reduction-per-piece", 0.08)
                : config.getDouble("armor.emerald.reduction-per-piece", 0.05);
    }

    @Override
    public String getId() {
        return id;
    }

    @Override
    public boolean isUnbreakable() {
        return reinforced;
    }

    @Override
    public double getDamageReductionPercent() {
        return reductionPercent;
    }

    @Override
    public double getDurabilityMultiplier() {
        return 1.5;
    }

    @Override
    public ItemStack build() {
        ItemBuilder builder = new ItemBuilder(slot.material)
                .emeraldName(slot.displayName, reinforced)
                .loreLine("&7Protection superieure au diamant.")
                .loreLine(reinforced ? "&7Incassable." : "&7Plus grande duree de vie que le diamant.")
                .blankLine()
                .progression(reinforced)
                .customId(id);
        if (reinforced) {
            builder.unbreakable(true);
        }
        return builder.build();
    }
}
""")
add("src/main/java/fr/faction/customitems/items/weapons/EmeraldSword.java", """package fr.faction.customitems.items.weapons;

import fr.faction.customitems.api.CustomItem;
import fr.faction.customitems.api.ExtraDurability;
import fr.faction.customitems.api.ItemBuilder;
import fr.faction.customitems.api.WeaponBonus;
import org.bukkit.Material;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.inventory.ItemStack;

public class EmeraldSword implements CustomItem, WeaponBonus, ExtraDurability {

    public static final String ID = "EMERALD_SWORD";
    private final double bonusDamage;

    public EmeraldSword(FileConfiguration config) {
        this.bonusDamage = config.getDouble("sword.emerald.bonus-damage", 3.0);
    }

    @Override
    public String getId() {
        return ID;
    }

    @Override
    public boolean isUnbreakable() {
        return false;
    }

    @Override
    public double getBonusDamage() {
        return bonusDamage;
    }

    @Override
    public double getDurabilityMultiplier() {
        return 1.5;
    }

    @Override
    public ItemStack build() {
        return new ItemBuilder(Material.DIAMOND_SWORD)
                .emeraldName("Epee", false)
                .loreLine("&7Inflige plus de degats qu'une epee en diamant.")
                .blankLine()
                .progression(false)
                .customId(ID)
                .build();
    }
}
""")

add("src/main/java/fr/faction/customitems/items/weapons/ReinforcedEmeraldSword.java", """package fr.faction.customitems.items.weapons;

import fr.faction.customitems.api.CustomItem;
import fr.faction.customitems.api.ItemBuilder;
import fr.faction.customitems.api.WeaponBonus;
import org.bukkit.Material;
import org.bukkit.configuration.file.FileConfiguration;
import org.bukkit.inventory.ItemStack;

public class ReinforcedEmeraldSword implements CustomItem, WeaponBonus {

    public static final String ID = "REINFORCED_EMERALD_SWORD";
    private final double bonusDamage;

    public ReinforcedEmeraldSword(FileConfiguration config) {
        this.bonusDamage = config.getDouble("sword.reinforced.bonus-damage", 5.0);
    }

    @Override
    public String getId() {
        return ID;
    }

    @Override
    public boolean isUnbreakable() {
        return true;
    }

    @Override
    public double getBonusDamage() {
        return bonusDamage;
    }

    @Override
    public ItemStack build() {
        return new ItemBuilder(Material.DIAMOND_SWORD)
                .emeraldName("Epee", true)
                .loreLine("&7Inflige plus de degats que l'epee emeraude.")
                .loreLine("&7Incassable.")
                .blankLine()
                .progression(true)
                .unbreakable(true)
                .customId(ID)
                .build();
    }
}
""")

add("src/main/java/fr/faction/customitems/items/misc/ReinforcedEmeraldBlock.java", """package fr.faction.customitems.items.misc;

import fr.faction.customitems.api.CustomItem;
import fr.faction.customitems.api.ItemBuilder;
import org.bukkit.Material;
import org.bukkit.inventory.ItemStack;

/**
 * Item de commerce sans capacite particuliere : sert de monnaie/objet de
 * valeur pour l'economie du serveur. Le NBT CustomItemId permet de le
 * distinguer d'un bloc d'emeraude vanilla classique (ex: pour des shops
 * qui ne doivent accepter que la version "officielle" du serveur).
 */
public class ReinforcedEmeraldBlock implements CustomItem {

    public static final String ID = "REINFORCED_EMERALD_BLOCK";

    @Override
    public String getId() {
        return ID;
    }

    @Override
    public boolean isUnbreakable() {
        return false;
    }

    @Override
    public ItemStack build() {
        return new ItemBuilder(Material.EMERALD_BLOCK)
                .emeraldName("Bloc d'emeraude renforce", true)
                .loreLine("&7Objet de commerce.")
                .loreLine("&7Aucune capacite speciale.")
                .blankLine()
                .customId(ID)
                .build();
    }
}
""")
add("src/main/java/fr/faction/customitems/registry/CustomItemRegistry.java", """package fr.faction.customitems.registry;

import fr.faction.customitems.api.CustomItem;
import fr.faction.customitems.items.armor.EmeraldArmorItem;
import fr.faction.customitems.items.misc.ReinforcedEmeraldBlock;
import fr.faction.customitems.items.tools.EmeraldAxe;
import fr.faction.customitems.items.tools.EmeraldHammer;
import fr.faction.customitems.items.tools.EmeraldHoe;
import fr.faction.customitems.items.tools.EmeraldPickaxe;
import fr.faction.customitems.items.tools.EmeraldShovel;
import fr.faction.customitems.items.tools.ReinforcedEmeraldAxe;
import fr.faction.customitems.items.tools.ReinforcedEmeraldHammer;
import fr.faction.customitems.items.tools.ReinforcedEmeraldHoe;
import fr.faction.customitems.items.tools.ReinforcedEmeraldPickaxe;
import fr.faction.customitems.items.tools.ReinforcedEmeraldShovel;
import fr.faction.customitems.items.weapons.EmeraldSword;
import fr.faction.customitems.items.weapons.ReinforcedEmeraldSword;
import org.bukkit.configuration.file.FileConfiguration;

import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

/**
 * Registre central de tous les custom items du plugin.
 *
 * Pour ajouter un nouvel item a l'avenir :
 *   1. Creer une classe implementant CustomItem (+ les marqueurs pertinents :
 *      MiningTool, ReplantingHoe, TreeFeller, WeaponBonus, ArmorBonus, ExtraDurability)
 *      dans le sous-package items.* approprie.
 *   2. Ajouter une ligne register(new MonNouvelItem(...)); ci-dessous.
 *   C'est la SEULE modification necessaire : les listeners lisent les
 *   marqueurs de facon generique et n'ont pas besoin d'etre modifies.
 */
public class CustomItemRegistry {

    private final Map<String, CustomItem> items = new LinkedHashMap<>();

    public CustomItemRegistry(FileConfiguration config) {
        // Outils
        register(new EmeraldHammer(config));
        register(new ReinforcedEmeraldHammer(config));
        register(new EmeraldHoe(config));
        register(new ReinforcedEmeraldHoe(config));
        register(new EmeraldPickaxe());
        register(new ReinforcedEmeraldPickaxe());
        register(new EmeraldShovel(config));
        register(new ReinforcedEmeraldShovel(config));
        register(new EmeraldAxe(config));
        register(new ReinforcedEmeraldAxe());

        // Armures (4 emplacements x 2 tiers)
        for (EmeraldArmorItem.Slot slot : EmeraldArmorItem.Slot.values()) {
            register(new EmeraldArmorItem(slot, false, config));
            register(new EmeraldArmorItem(slot, true, config));
        }

        // Armes
        register(new EmeraldSword(config));
        register(new ReinforcedEmeraldSword(config));

        // Commerce
        register(new ReinforcedEmeraldBlock());
    }

    private void register(CustomItem item) {
        items.put(item.getId().toUpperCase(Locale.ROOT), item);
    }

    public Optional<CustomItem> get(String id) {
        if (id == null) return Optional.empty();
        return Optional.ofNullable(items.get(id.toUpperCase(Locale.ROOT)));
    }

    public Collection<CustomItem> getAll() {
        return items.values();
    }

    public Set<String> getIds() {
        return items.keySet();
    }
}
""")

add("src/main/java/fr/faction/customitems/manager/CustomItemManager.java", """package fr.faction.customitems.manager;

import fr.faction.customitems.api.CustomItem;
import fr.faction.customitems.nbt.NBTEditor;
import fr.faction.customitems.registry.CustomItemRegistry;
import org.bukkit.entity.Player;
import org.bukkit.inventory.ItemStack;

import java.util.Optional;

/**
 * Point d'entree principal pour identifier et distribuer des custom items.
 * Utilise par la commande /citem et par les listeners.
 */
public class CustomItemManager {

    private final CustomItemRegistry registry;

    public CustomItemManager(CustomItemRegistry registry) {
        this.registry = registry;
    }

    public CustomItemRegistry getRegistry() {
        return registry;
    }

    /** @return true si l'ItemStack porte un tag NBT CustomItemId connu du registre. */
    public boolean isCustomItem(ItemStack item) {
        return getId(item) != null;
    }

    /** @return l'identifiant interne stocke dans le NBT de l'item, ou null. */
    public String getId(ItemStack item) {
        if (item == null) {
            return null;
        }
        return NBTEditor.getCustomId(item);
    }

    /** @return la definition CustomItem correspondant a l'ItemStack donne, si presente en NBT et connue du registre. */
    public Optional<CustomItem> getCustomItem(ItemStack item) {
        String id = getId(item);
        if (id == null) {
            return Optional.empty();
        }
        return registry.get(id);
    }

    /**
     * Donne `amount` exemplaires de l'item `id` au joueur.
     * @return true si l'id existait dans le registre.
     */
    public boolean give(Player player, String id, int amount) {
        Optional<CustomItem> opt = registry.get(id);
        if (!opt.isPresent()) {
            return false;
        }
        CustomItem definition = opt.get();
        for (int i = 0; i < amount; i++) {
            ItemStack stack = definition.build();
            player.getInventory().addItem(stack).values()
                    .forEach(leftover -> player.getWorld().dropItemNaturally(player.getLocation(), leftover));
        }
        return true;
    }
}
""")
add("src/main/java/fr/faction/customitems/hook/ProtectionHook.java", """package fr.faction.customitems.hook;

import org.bukkit.Bukkit;
import org.bukkit.block.Block;
import org.bukkit.entity.Player;
import org.bukkit.event.block.BlockBreakEvent;

/**
 * Verifie si un joueur est autorise a casser un bloc AVANT toute destruction
 * automatique declenchee par un custom item (hammer, pelle, tree capitator...).
 *
 * Technique utilisee : au lieu de dependre "en dur" de Factions ou de
 * WorldGuard (ce qui obligerait a lier le plugin a une API precise et a la
 * maintenir a chaque changement de version de ces plugins tiers), on emet
 * un BlockBreakEvent "sonde" pour le joueur et le bloc concerne, sans
 * jamais casser reellement le bloc avec cet event. Tous les plugins de
 * protection presents sur le serveur (Factions, FactionsUUID, WorldGuard,
 * GriefPrevention, Towny, etc.) ecoutent deja BlockBreakEvent et l'annulent
 * (event.setCancelled(true)) si le joueur n'a pas la permission de casser
 * a cet endroit. Il suffit donc de lire event.isCancelled() apres l'appel
 * pour savoir, de facon totalement generique, si la destruction reelle
 * (via Block#breakNaturally) doit avoir lieu.
 *
 * Cette approche garantit la compatibilite avec N'IMPORTE QUEL plugin de
 * protection sans dependance de compilation, conformement a la regle du
 * cahier des charges : "Avant chaque destruction automatique : verifier si
 * le joueur peut casser le bloc."
 */
public final class ProtectionHook {

    private ProtectionHook() {
    }

    public static boolean canBreak(Player player, Block block) {
        BlockBreakEvent probe = new BlockBreakEvent(block, player);
        Bukkit.getPluginManager().callEvent(probe);
        return !probe.isCancelled();
    }
}
""")
add("src/main/java/fr/faction/customitems/util/AreaBreakUtil.java", """package fr.faction.customitems.util;

import org.bukkit.block.Block;
import org.bukkit.block.BlockFace;
import org.bukkit.entity.Player;
import org.bukkit.util.Vector;

import java.util.ArrayList;
import java.util.List;

/**
 * Calcule les zones de blocs (plan perpendiculaire au regard du joueur)
 * utilisees par les outils de zone (hammer, pelle).
 */
public final class AreaBreakUtil {

    private AreaBreakUtil() {
    }

    /** Determine la face regardee par le joueur (haut/bas/nord/sud/est/ouest). */
    public static BlockFace getFace(Player player) {
        Vector dir = player.getLocation().getDirection();
        double x = Math.abs(dir.getX());
        double y = Math.abs(dir.getY());
        double z = Math.abs(dir.getZ());

        if (y > x && y > z) {
            return dir.getY() > 0 ? BlockFace.UP : BlockFace.DOWN;
        } else if (x > z) {
            return dir.getX() > 0 ? BlockFace.EAST : BlockFace.WEST;
        } else {
            return dir.getZ() > 0 ? BlockFace.SOUTH : BlockFace.NORTH;
        }
    }

    /**
     * @return tous les blocs du plan perpendiculaire a `face`, centres sur
     * `center`, sur un rayon donne (1 = 3x3, 2 = 5x5), sans inclure `center`.
     */
    public static List<Block> getPlaneArea(Block center, BlockFace face, int radius) {
        List<Block> blocks = new ArrayList<>();
        for (int a = -radius; a <= radius; a++) {
            for (int b = -radius; b <= radius; b++) {
                if (a == 0 && b == 0) {
                    continue;
                }
                Block relative;
                switch (face) {
                    case UP:
                    case DOWN:
                        relative = center.getRelative(a, 0, b);
                        break;
                    case EAST:
                    case WEST:
                        relative = center.getRelative(0, a, b);
                        break;
                    default:
                        relative = center.getRelative(a, b, 0);
                        break;
                }
                blocks.add(relative);
            }
        }
        return blocks;
    }
}
""")
add("src/main/java/fr/faction/customitems/listener/MiningListener.java", """package fr.faction.customitems.listener;

import fr.faction.customitems.api.CustomItem;
import fr.faction.customitems.api.MiningTool;
import fr.faction.customitems.api.TreeFeller;
import fr.faction.customitems.hook.ProtectionHook;
import fr.faction.customitems.items.tools.EmeraldAxe;
import fr.faction.customitems.items.tools.EmeraldShovel;
import fr.faction.customitems.items.tools.ReinforcedEmeraldShovel;
import fr.faction.customitems.manager.CustomItemManager;
import fr.faction.customitems.util.AreaBreakUtil;
import org.bukkit.Material;
import org.bukkit.block.Block;
import org.bukkit.block.BlockFace;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.inventory.ItemStack;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.EnumSet;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;

/**
 * Gere la destruction de zone pour le Hammer et la Pelle, la colonne 1x3
 * pour la Hache emeraude simple, et le Tree Capitator pour la Hache emeraude
 * renforcee. La Pioche emeraude n'a pas de comportement special ici (elle
 * casse normalement un seul bloc, plus vite, comme n'importe quel outil).
 *
 * Toutes les destructions automatiques passent par ProtectionHook.canBreak
 * avant Block#breakNaturally, conformement a la regle du cahier des charges.
 */
public class MiningListener implements Listener {

    private static final Set<Material> SHOVEL_COMPATIBLE = EnumSet.of(
            Material.DIRT, Material.GRASS, Material.SAND, Material.GRAVEL,
            Material.CLAY, Material.SOIL, Material.MYCEL, Material.SOUL_SAND, Material.SNOW_BLOCK
    );

    private static final Set<Material> LOG_TYPES = EnumSet.of(Material.LOG, Material.LOG_2);

    private static final int TREE_FELLER_MAX_BLOCKS = 256;

    private final CustomItemManager manager;

    public MiningListener(CustomItemManager manager) {
        this.manager = manager;
    }

    @EventHandler(priority = EventPriority.HIGH, ignoreCancelled = true)
    public void onBlockBreak(BlockBreakEvent event) {
        Player player = event.getPlayer();
        ItemStack hand = player.getItemInHand();
        Optional<CustomItem> opt = manager.getCustomItem(hand);
        if (!opt.isPresent()) {
            return;
        }

        CustomItem custom = opt.get();
        Block center = event.getBlock();
        Material originalType = center.getType();

        if (custom instanceof TreeFeller) {
            if (LOG_TYPES.contains(originalType)) {
                handleTreeFeller(player, center, hand);
            }
            return;
        }

        if (!(custom instanceof MiningTool)) {
            return;
        }

        MiningTool tool = (MiningTool) custom;
        if (tool.getRadius() <= 0) {
            return;
        }

        if (custom.getId().equals(EmeraldAxe.ID)) {
            if (!LOG_TYPES.contains(originalType)) {
                return;
            }
            handleColumn(player, center, originalType, tool.getRadius(), hand);
            return;
        }

        boolean isShovel = custom.getId().equals(EmeraldShovel.ID) || custom.getId().equals(ReinforcedEmeraldShovel.ID);
        if (isShovel && !SHOVEL_COMPATIBLE.contains(originalType)) {
            return;
        }

        BlockFace face = AreaBreakUtil.getFace(player);
        List<Block> area = AreaBreakUtil.getPlaneArea(center, face, tool.getRadius());
        breakArea(player, area, originalType, tool.sameBlockTypeOnly(), hand);
    }

    private void breakArea(Player player, List<Block> blocks, Material requiredType, boolean sameTypeOnly, ItemStack tool) {
        for (Block block : blocks) {
            if (block.getType() == Material.AIR) {
                continue;
            }
            if (sameTypeOnly && block.getType() != requiredType) {
                continue;
            }
            if (!ProtectionHook.canBreak(player, block)) {
                continue;
            }
            block.breakNaturally(tool);
        }
    }

    private void handleColumn(Player player, Block center, Material requiredType, int length, ItemStack tool) {
        Block current = center;
        for (int i = 1; i < length; i++) {
            current = current.getRelative(BlockFace.UP);
            if (current.getType() != requiredType) {
                break;
            }
            if (!ProtectionHook.canBreak(player, current)) {
                continue;
            }
            current.breakNaturally(tool);
        }
    }

    private void handleTreeFeller(Player player, Block origin, ItemStack tool) {
        Material logType = origin.getType();
        Set<Block> visited = new HashSet<>();
        Deque<Block> queue = new ArrayDeque<>();
        queue.add(origin);
        visited.add(origin);

        int processed = 0;
        BlockFace[] directions = {BlockFace.UP, BlockFace.DOWN, BlockFace.NORTH, BlockFace.SOUTH, BlockFace.EAST, BlockFace.WEST};

        while (!queue.isEmpty() && processed < TREE_FELLER_MAX_BLOCKS) {
            Block current = queue.poll();
            processed++;

            if (!current.equals(origin)) {
                if (ProtectionHook.canBreak(player, current)) {
                    current.breakNaturally(tool);
                }
            }

            for (BlockFace face : directions) {
                Block neighbor = current.getRelative(face);
                if (visited.contains(neighbor)) {
                    continue;
                }
                if (neighbor.getType() == logType) {
                    visited.add(neighbor);
                    queue.add(neighbor);
                }
            }
        }
    }
}
""")
add("src/main/java/fr/faction/customitems/listener/FarmingListener.java", """package fr.faction.customitems.listener;

import fr.faction.customitems.api.CustomItem;
import fr.faction.customitems.api.ReplantingHoe;
import fr.faction.customitems.hook.ProtectionHook;
import fr.faction.customitems.manager.CustomItemManager;
import fr.faction.customitems.util.AreaBreakUtil;
import org.bukkit.CropState;
import org.bukkit.Material;
import org.bukkit.block.Block;
import org.bukkit.block.BlockFace;
import org.bukkit.block.BlockState;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.material.Crops;
import org.bukkit.material.MaterialData;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Gere la recolte + replantation automatique des houes emeraude.
 *
 * Ble, carottes et pommes de terre sont nativement presents en 1.8.x.
 * La betterave (Beetroot) n'existe qu'a partir de Minecraft 1.9 : son
 * support est enregistre de facon defensive (putIfExists) et s'activera
 * automatiquement sans modification de code si ce plugin tourne un jour
 * sur une version plus recente ; sur un serveur strictement 1.8.x elle est
 * simplement ignoree (aucune erreur, aucun crash).
 */
public class FarmingListener implements Listener {

    private static final Map<Material, Material> CROP_TO_SEED = new HashMap<>();

    static {
        CROP_TO_SEED.put(Material.CROPS, Material.SEEDS);
        CROP_TO_SEED.put(Material.CARROT, Material.CARROT_ITEM);
        CROP_TO_SEED.put(Material.POTATO, Material.POTATO_ITEM);
        putIfExists("BEETROOT_BLOCK", "BEETROOT_SEEDS");
    }

    private static void putIfExists(String cropName, String seedName) {
        try {
            Material crop = Material.valueOf(cropName);
            Material seed = Material.valueOf(seedName);
            CROP_TO_SEED.put(crop, seed);
        } catch (IllegalArgumentException ex) {
            // Culture indisponible sur cette version du serveur : ignoree silencieusement.
        }
    }

    private final CustomItemManager manager;

    public FarmingListener(CustomItemManager manager) {
        this.manager = manager;
    }

    @EventHandler(priority = EventPriority.HIGH, ignoreCancelled = true)
    public void onCropBreak(BlockBreakEvent event) {
        Block block = event.getBlock();
        Material cropType = block.getType();
        if (!CROP_TO_SEED.containsKey(cropType) || !isFullyGrown(block)) {
            return;
        }

        Player player = event.getPlayer();
        ItemStack hand = player.getItemInHand();
        Optional<CustomItem> opt = manager.getCustomItem(hand);
        if (!opt.isPresent() || !(opt.get() instanceof ReplantingHoe)) {
            return;
        }

        ReplantingHoe hoe = (ReplantingHoe) opt.get();
        Material seed = CROP_TO_SEED.get(cropType);

        // On gere nous-memes la destruction + replantation du bloc central :
        // on annule l'event vanilla pour eviter un double traitement du bloc.
        event.setCancelled(true);
        replant(player, block, cropType, seed);

        if (hoe.getRadius() > 0) {
            BlockFace face = AreaBreakUtil.getFace(player);
            List<Block> area = AreaBreakUtil.getPlaneArea(block, face, hoe.getRadius());
            for (Block other : area) {
                if (other.getType() != cropType || !isFullyGrown(other)) {
                    continue;
                }
                if (!ProtectionHook.canBreak(player, other)) {
                    continue;
                }
                replant(player, other, cropType, seed);
            }
        }
    }

    private boolean isFullyGrown(Block block) {
        MaterialData data = block.getState().getData();
        if (data instanceof Crops) {
            return ((Crops) data).getState() == CropState.RIPE;
        }
        return true;
    }

    /** Casse naturellement le bloc (drops normaux) puis le replante si le joueur possede la graine. */
    private void replant(Player player, Block block, Material cropType, Material seedItem) {
        ItemStack tool = player.getItemInHand();
        block.breakNaturally(tool);

        if (!consumeSeed(player, seedItem)) {
            return; // pas de graine : recolte simple, sans replantation
        }

        block.setType(cropType);
        BlockState state = block.getState();
        MaterialData data = state.getData();
        if (data instanceof Crops) {
            ((Crops) data).setState(CropState.SEEDED);
            state.setData(data);
            state.update(true, false);
        }
    }

    private boolean consumeSeed(Player player, Material seedItem) {
        ItemStack probe = new ItemStack(seedItem, 1);
        if (!player.getInventory().containsAtLeast(probe, 1)) {
            return false;
        }
        player.getInventory().removeItem(probe);
        return true;
    }
}
""")
add("src/main/java/fr/faction/customitems/listener/CombatListener.java", """package fr.faction.customitems.listener;

import fr.faction.customitems.api.ArmorBonus;
import fr.faction.customitems.api.CustomItem;
import fr.faction.customitems.api.WeaponBonus;
import fr.faction.customitems.manager.CustomItemManager;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntityDamageByEntityEvent;
import org.bukkit.event.entity.EntityDamageEvent;
import org.bukkit.inventory.ItemStack;

import java.util.Optional;

/**
 * Applique le bonus de degats des epees emeraude et la reduction de degats
 * supplementaire des armures emeraude.
 *
 * Pourquoi une gestion manuelle et pas des attribute modifiers ? L'API
 * Bukkit 1.8 ne propose pas encore ItemMeta#addAttributeModifier (introduit
 * en 1.13). Le bonus est donc calcule et applique directement sur les
 * evenements de degats, ce qui reste totalement compatible avec les
 * custom enchants d'autres plugins (ils s'appliquent normalement avant/apres
 * dans la chaine d'evenements selon leur propre priorite).
 */
public class CombatListener implements Listener {

    /** Securite anti-abus : la reduction cumulee de toutes les pieces d'armure ne peut jamais depasser 80%. */
    private static final double MAX_ARMOR_REDUCTION = 0.80;

    private final CustomItemManager manager;

    public CombatListener(CustomItemManager manager) {
        this.manager = manager;
    }

    @EventHandler(priority = EventPriority.NORMAL, ignoreCancelled = true)
    public void onWeaponDamage(EntityDamageByEntityEvent event) {
        if (!(event.getDamager() instanceof Player)) {
            return;
        }
        Player attacker = (Player) event.getDamager();
        ItemStack hand = attacker.getItemInHand();

        Optional<CustomItem> opt = manager.getCustomItem(hand);
        if (opt.isPresent() && opt.get() instanceof WeaponBonus) {
            double bonus = ((WeaponBonus) opt.get()).getBonusDamage();
            event.setDamage(event.getDamage() + bonus);
        }
    }

    @EventHandler(priority = EventPriority.HIGH, ignoreCancelled = true)
    public void onArmorReduction(EntityDamageEvent event) {
        if (!(event.getEntity() instanceof Player)) {
            return;
        }
        Player victim = (Player) event.getEntity();

        double totalReduction = 0.0;
        for (ItemStack armorPiece : victim.getInventory().getArmorContents()) {
            if (armorPiece == null) {
                continue;
            }
            Optional<CustomItem> opt = manager.getCustomItem(armorPiece);
            if (opt.isPresent() && opt.get() instanceof ArmorBonus) {
                totalReduction += ((ArmorBonus) opt.get()).getDamageReductionPercent();
            }
        }

        if (totalReduction <= 0) {
            return;
        }
        totalReduction = Math.min(totalReduction, MAX_ARMOR_REDUCTION);
        event.setDamage(event.getDamage() * (1.0 - totalReduction));
    }
}
""")

add("src/main/java/fr/faction/customitems/listener/ItemDurabilityListener.java", """package fr.faction.customitems.listener;

import fr.faction.customitems.api.CustomItem;
import fr.faction.customitems.api.ExtraDurability;
import fr.faction.customitems.manager.CustomItemManager;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.player.PlayerItemDamageEvent;

import java.util.Optional;
import java.util.Random;

/**
 * Fait respecter la regle "items renforces = incassables" (filet de securite
 * en plus du tag NBT Unbreakable) et simule la duree de vie superieure des
 * items emeraude de base via ExtraDurability.
 */
public class ItemDurabilityListener implements Listener {

    private final CustomItemManager manager;
    private final Random random = new Random();

    public ItemDurabilityListener(CustomItemManager manager) {
        this.manager = manager;
    }

    @EventHandler(priority = EventPriority.HIGH, ignoreCancelled = true)
    public void onItemDamage(PlayerItemDamageEvent event) {
        Optional<CustomItem> opt = manager.getCustomItem(event.getItem());
        if (!opt.isPresent()) {
            return;
        }
        CustomItem custom = opt.get();

        if (custom.isUnbreakable()) {
            event.setCancelled(true);
            return;
        }

        if (custom instanceof ExtraDurability) {
            double multiplier = ((ExtraDurability) custom).getDurabilityMultiplier();
            double cancelChance = 1.0 - (1.0 / multiplier);
            if (random.nextDouble() < cancelChance) {
                event.setCancelled(true);
            }
        }
    }
}
""")
add("src/main/java/fr/faction/customitems/listener/CustomItemListener.java", """package fr.faction.customitems.listener;

import fr.faction.customitems.manager.CustomItemManager;
import org.bukkit.event.EventHandler;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.event.inventory.PrepareItemCraftEvent;
import org.bukkit.inventory.ItemStack;

/**
 * Protections generiques transverses a tous les custom items :
 * empeche qu'un custom item soit utilise comme ingredient dans une recette
 * de craft vanilla (ce qui ferait perdre son NBT/son identite ou permettrait
 * des exploits de duplication de stats).
 */
public class CustomItemListener implements Listener {

    private final CustomItemManager manager;

    public CustomItemListener(CustomItemManager manager) {
        this.manager = manager;
    }

    @EventHandler(priority = EventPriority.HIGH)
    public void onPrepareCraft(PrepareItemCraftEvent event) {
        for (ItemStack ingredient : event.getInventory().getMatrix()) {
            if (ingredient == null) {
                continue;
            }
            if (manager.isCustomItem(ingredient)) {
                event.getInventory().setResult(null);
                return;
            }
        }
    }
}
""")

add("src/main/java/fr/faction/customitems/command/CustomItemCommand.java", """package fr.faction.customitems.command;

import fr.faction.customitems.api.CustomItem;
import fr.faction.customitems.manager.CustomItemManager;
import fr.faction.customitems.util.ColorUtil;
import org.bukkit.Bukkit;
import org.bukkit.command.Command;
import org.bukkit.command.CommandExecutor;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabCompleter;
import org.bukkit.entity.Player;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.stream.Collectors;

/**
 * /citem give <joueur> <id> [quantite]
 * /citem list
 * /citem id            (affiche l'id du custom item tenu en main)
 */
public class CustomItemCommand implements CommandExecutor, TabCompleter {

    private final CustomItemManager manager;

    public CustomItemCommand(CustomItemManager manager) {
        this.manager = manager;
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (args.length == 0) {
            sender.sendMessage(ColorUtil.c("&7Usage: &f/citem give <joueur> <id> [quantite] &7| &f/citem list &7| &f/citem id"));
            return true;
        }

        String sub = args[0].toLowerCase(Locale.ROOT);

        switch (sub) {
            case "give":
                return handleGive(sender, args);
            case "list":
                return handleList(sender);
            case "id":
                return handleId(sender);
            default:
                sender.sendMessage(ColorUtil.c("&cSous-commande inconnue. Usage: /citem give|list|id"));
                return true;
        }
    }

    private boolean handleGive(CommandSender sender, String[] args) {
        if (args.length < 3) {
            sender.sendMessage(ColorUtil.c("&cUsage: /citem give <joueur> <id> [quantite]"));
            return true;
        }
        Player target = Bukkit.getPlayerExact(args[1]);
        if (target == null) {
            sender.sendMessage(ColorUtil.c("&cJoueur introuvable ou hors ligne : " + args[1]));
            return true;
        }
        String id = args[2];
        int amount = 1;
        if (args.length >= 4) {
            try {
                amount = Math.max(1, Integer.parseInt(args[3]));
            } catch (NumberFormatException ex) {
                sender.sendMessage(ColorUtil.c("&cQuantite invalide : " + args[3]));
                return true;
            }
        }

        boolean success = manager.give(target, id, amount);
        if (!success) {
            sender.sendMessage(ColorUtil.c("&cIdentifiant de custom item inconnu : " + id));
            return true;
        }

        sender.sendMessage(ColorUtil.c("&aDonne " + amount + "x " + id + " a " + target.getName() + "."));
        if (!sender.equals(target)) {
            target.sendMessage(ColorUtil.c("&aVous avez recu " + amount + "x " + id + "."));
        }
        return true;
    }

    private boolean handleList(CommandSender sender) {
        String ids = manager.getRegistry().getIds().stream().collect(Collectors.joining(", "));
        sender.sendMessage(ColorUtil.c("&7Custom items disponibles : &f" + ids));
        return true;
    }

    private boolean handleId(CommandSender sender) {
        if (!(sender instanceof Player)) {
            sender.sendMessage(ColorUtil.c("&cCette sous-commande n'est utilisable que par un joueur."));
            return true;
        }
        Player player = (Player) sender;
        String id = manager.getId(player.getItemInHand());
        if (id == null) {
            sender.sendMessage(ColorUtil.c("&7L'item en main n'est pas un custom item."));
        } else {
            sender.sendMessage(ColorUtil.c("&7Identifiant : &f" + id));
        }
        return true;
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String alias, String[] args) {
        List<String> completions = new ArrayList<>();
        if (args.length == 1) {
            completions.addAll(java.util.Arrays.asList("give", "list", "id"));
        } else if (args.length == 2 && args[0].equalsIgnoreCase("give")) {
            for (Player p : Bukkit.getOnlinePlayers()) {
                completions.add(p.getName());
            }
        } else if (args.length == 3 && args[0].equalsIgnoreCase("give")) {
            completions.addAll(manager.getRegistry().getIds());
        }

        String current = args.length > 0 ? args[args.length - 1].toLowerCase(Locale.ROOT) : "";
        return completions.stream()
                .filter(s -> s.toLowerCase(Locale.ROOT).startsWith(current))
                .collect(Collectors.toList());
    }
}
""")
add("src/main/java/fr/faction/customitems/CustomItemsPlugin.java", """package fr.faction.customitems;

import fr.faction.customitems.command.CustomItemCommand;
import fr.faction.customitems.listener.CombatListener;
import fr.faction.customitems.listener.CustomItemListener;
import fr.faction.customitems.listener.FarmingListener;
import fr.faction.customitems.listener.ItemDurabilityListener;
import fr.faction.customitems.listener.MiningListener;
import fr.faction.customitems.manager.CustomItemManager;
import fr.faction.customitems.nbt.NBTEditor;
import fr.faction.customitems.registry.CustomItemRegistry;
import org.bukkit.command.PluginCommand;
import org.bukkit.plugin.java.JavaPlugin;

/**
 * Point d'entree du plugin. Cablage de l'ensemble du systeme :
 * registry -> manager -> listeners -> commande.
 *
 * Pour ajouter un nouvel item : voir CustomItemRegistry.
 * Pour ajouter un nouveau comportement : creer un marqueur dans le package
 * api, l'implementer sur l'item concerne, puis lire ce marqueur depuis le
 * listener pertinent (ou en creer un nouveau si le comportement est inedit).
 */
public class CustomItemsPlugin extends JavaPlugin {

    private CustomItemManager customItemManager;

    @Override
    public void onEnable() {
        saveDefaultConfig();

        if (!NBTEditor.isAvailable()) {
            getLogger().warning("NBTEditor indisponible sur cette version de serveur : "
                    + "les fonctionnalites Unbreakable/identification NBT seront degradees.");
        }

        CustomItemRegistry registry = new CustomItemRegistry(getConfig());
        this.customItemManager = new CustomItemManager(registry);

        getServer().getPluginManager().registerEvents(new MiningListener(customItemManager), this);
        getServer().getPluginManager().registerEvents(new FarmingListener(customItemManager), this);
        getServer().getPluginManager().registerEvents(new CombatListener(customItemManager), this);
        getServer().getPluginManager().registerEvents(new ItemDurabilityListener(customItemManager), this);
        getServer().getPluginManager().registerEvents(new CustomItemListener(customItemManager), this);

        CustomItemCommand commandExecutor = new CustomItemCommand(customItemManager);
        PluginCommand citem = getCommand("citem");
        if (citem != null) {
            citem.setExecutor(commandExecutor);
            citem.setTabCompleter(commandExecutor);
        }

        getLogger().info("CustomItems active - " + registry.getIds().size() + " items enregistres.");
    }

    @Override
    public void onDisable() {
        getLogger().info("CustomItems desactive.");
    }

    public CustomItemManager getCustomItemManager() {
        return customItemManager;
    }
}
""")
add("README.md", """# CustomItems - Systeme de custom items tier Emeraude (Spigot 1.8.x)

Plugin complet pour serveur PvP Faction Spigot 1.8.x ajoutant une
progression d'equipements superieure au diamant (tier Emeraude, puis
Emeraude renforcee).

## Compilation

Prerequis : Java 8+, Maven, et Spigot 1.8.8 installe dans votre repo Maven
local (via BuildTools.jar) :

    java -jar BuildTools.jar --rev 1.8.8

Puis, a la racine du projet :

    mvn clean package

Le jar compile se trouve dans `target/CustomItems.jar`. Placez-le dans le
dossier `plugins/` de votre serveur Spigot 1.8.x.

## Architecture

- `api/` - Contrats (CustomItem) et marqueurs de comportement (MiningTool,
  ReplantingHoe, TreeFeller, WeaponBonus, ArmorBonus, ExtraDurability),
  ainsi que ItemBuilder (construction des ItemStack) et le format visuel
  impose par le cahier des charges.
- `nbt/` - NBTEditor : acces reflexif au NBT (Unbreakable, identifiant interne),
  necessaire car l'API Bukkit 1.8 ne propose ni setUnbreakable() (1.11+) ni
  PersistentDataContainer (1.14+).
- `registry/` - CustomItemRegistry : liste centrale de tous les items. C'est
  le SEUL endroit a modifier pour ajouter un nouvel item.
- `manager/` - CustomItemManager : identification et distribution des items.
- `items/tools|armor|weapons|misc/` - Implementations concretes des 21 items.
- `listener/` - MiningListener (hammer/pelle/hache/tree capitator),
  FarmingListener (houes), CombatListener (epees/armures), ItemDurabilityListener
  (Unbreakable + duree de vie), CustomItemListener (anti-exploits generiques).
- `hook/ProtectionHook` - Verification generique des protections (Factions,
  WorldGuard, GriefPrevention, etc.) via une sonde BlockBreakEvent, sans
  dependance de compilation a un plugin de protection precis.
- `command/CustomItemCommand` - /citem give|list|id.

## Ajouter un nouvel item

1. Creer une classe implementant `CustomItem` (+ les marqueurs pertinents)
   dans le sous-package `items.*` approprie.
2. L'enregistrer dans `CustomItemRegistry`.

Aucune autre modification n'est necessaire : les listeners lisent les
marqueurs de facon generique.

## Notes de conception importantes

- Les armures/armes/outils emeraude utilisent les materiaux DIAMOND_* comme
  base (stats vanilla deja superieures), et le bonus "superieur au diamant"
  est applique manuellement (CombatListener) car Bukkit 1.8 ne propose pas
  d'attribute modifiers (introduits en 1.13).
- La betterave (houe) n'existe qu'a partir de Minecraft 1.9 ; son support est
  enregistre de facon defensive et s'active automatiquement si le serveur
  est mis a jour, sans erreur sur un serveur strictement 1.8.x.
- Toute destruction automatique de bloc (hammer, pelle, tree capitator) passe
  par ProtectionHook.canBreak() avant Block#breakNaturally(), conformement a
  la regle du cahier des charges sur le respect des protections serveur.
""")

def main():
    base = os.path.join(os.getcwd(), "CustomItems")
    for rel_path, content in FILES.items():
        full_path = os.path.join(base, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Cree :", full_path)
    print()
    print("Termine.", len(FILES), "fichiers crees dans", base)

if __name__ == "__main__":
    main()
