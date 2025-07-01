<?php
// 1. CONNECT TO DATABASE
$conn = new mysqli("localhost", "root", "", "rahasoft");

// Check for error
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// 2. FETCH CATEGORIES FROM DATABASE
$categories = $conn->query("SELECT id, name FROM categories");
?>

<!DOCTYPE html>
<html>
<head>
    <title>Add New Product</title>
</head>
<body>
    <h2>Add New Product</h2>

    <form method="POST" action="save_product.php">
        <label>Product Name:</label><br>
        <input type="text" name="name" required><br><br>

        <label>Category:</label><br>
        <select name="category_id" required>
            <option value="">-- Select Category --</option>
            <?php while($row = $categories->fetch_assoc()): ?>
                <option value="<?= $row['id'] ?>"><?= $row['name'] ?></option>
            <?php endwhile; ?>
        </select><br><br>

        <label>Unit Price:</label><br>
        <input type="number" name="unit_price" step="0.01" required><br><br>

        <label>Stock Quantity:</label><br>
        <input type="number" name="stock_quantity" required><br><br>

        <button type="submit">Save Product</button>
    </form>
</body>
</html>
