# INDUSTRY VERTICALS REFERENCE
## Industry-Standard Relational Schema

---

## DATABASE TABLES (Industry Standard)

### 1. production_methods
| id | name | description |
|---|---|---|
| rtw | Ready-To-Wear | Off-the-shelf standard sizing |
| mtm | Made-To-Measure | Custom-made to individual measurements |
| custom | Custom Apparel | Team/specialty customization |

### 2. product_categories
| id | name | parent_category |
|---|---|---|
| casual | Casual Wear | NULL |
| sportswear | Sportswear & Athleisure | NULL |
| denim | Denim & Indigo | NULL |
| kidswear | Kidswear | NULL |
| modest | Modest Fashion | NULL |
| sustainable | Sustainable Fashion | NULL |
| corporate | Corporate Attire | NULL |
| bridal | Bridal & Tuxedo | NULL |
| outerwear | Outerwear & Jackets | NULL |
| workwear | Workwear & Industrial | NULL |
| healthcare | Healthcare & Fitness | NULL |
| uniforms | Uniforms | NULL |
| fashion_tech | Fashion Technology | NULL |
| theatrical | Theatrical Costuming | NULL |

### 3. cultural_attire (Country-Specific MTM Context)
| id | name | country_code | region | description |
|---|---|---|---|---|
| bespoke_eu | Bespoke Suits | IT | Europe | Italian/European bespoke |
| savile_row | Savile Row Bespoke | GB | Europe | British bespoke |
| haute_couture | Haute Couture | FR | Europe | French high fashion |
| cheongsam | Cheongsam/Qipao | CN | Asia | Chinese traditional |
| kimono | Kimono | JP | Asia | Japanese traditional |
| shervani | Shervani/Lehenga | IN | Asia | Indian formal wear |
| hanbok | Hanbok | KR | Asia | Korean traditional |
| agbada | Agbada/Dashiki | NG | Africa | Nigerian formal |
| kente | Kente | GH | Africa | Ghanaian traditional |
| kilt | Kilt | GB | Europe | Scottish formal |
| thobe | Thobe/Kandura | AE | Middle East | Middle Eastern |
| shalwar | Shalwar Kameez | PK | Asia | South Asian |
| batik | Batik/Kebaya | ID | Asia | Indonesian |
| sari | Sari | IN | Asia | Indian drape |

### 4. industry_verticals
| id | name | category_type |
|---|---|---|
| rtw | Ready-To-Wear | production |
| mtm | Made-To-Measure | production |
| custom | Custom Apparel | production |
| bridal | Bridal & Tuxedo | product |
| outerwear | Outerwear & Jackets | product |
| workwear | Workwear & Industrial | product |
| fashion_tech | Fashion Technology | tech |

### 5. vertical_products (junction)
| vertical_id | product_category_id |
|---|---|
| rtw | casual, sportswear, denim, kidswear, modest, sustainable, corporate |
| mtm | casual, corporate |
| custom | uniforms, theatrical |
| bridal | bridal |
| outerwear | outerwear |
| workwear | workwear, healthcare, uniforms |
| fashion_tech | fashion_tech |

### 6. vertical_country_context (MTM Mappings)
| vertical_id | country_code | cultural_attire_id | is_primary |
|---|---|---|---|
| mtm | IT | bespoke_eu | TRUE |
| mtm | GB | savile_row | TRUE |
| mtm | FR | haute_couture | TRUE |
| mtm | CN | cheongsam | TRUE |
| mtm | JP | kimono | TRUE |
| mtm | IN | shervani | TRUE |
| mtm | KR | hanbok | TRUE |
| mtm | NG | agbada | TRUE |
| mtm | GH | kente | TRUE |
| mtm | AE | thobe | TRUE |
| mtm | PK | shalwar | TRUE |
| mtm | ID | batik | TRUE |

---

## RELATIONAL QUERIES

### Get MTM options for a country:
```sql
SELECT v.name, ca.name, ca.description
FROM vertical_country_context vcc
JOIN industry_verticals v ON v.id = vcc.vertical_id
JOIN cultural_attire ca ON ca.id = vcc.cultural_attire_id
WHERE vcc.country_code = 'IN';
```

### Get all products for a vertical:
```sql
SELECT v.name, pc.name
FROM vertical_products vp
JOIN industry_verticals v ON v.id = vp.vertical_id
JOIN product_categories pc ON pc.id = vp.product_category_id;
```
