<?php include('header.php'); ?>

<?php
require('../model/database.php');
require('../model/award_db.php');

if (isset($_POST['submit'])) {
  try {
    require "common.php";

    $connection = new PDO($dsn, $username, $password);
    $connection->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    $covid_status = $_POST['covid_status'];
    $amount_range = $_POST['amount_range'];

    $result = lookup_covid($covid_status, $amount_range);
  } catch(PDOException $error) {
    echo $sql . "<br>" . $error->getMessage();
  }
}
?>

<!DOCTYPE html>
<html>
<head>
  <style>
    body {
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      margin: 0;
      font-family: Arial, sans-serif;
      background-color: #f4f4f4;
    }
    .container {
      background-color: #fff;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
      width: 100%;
      max-width: 600px;
      text-align: center;
    }
    form {
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-bottom: 20px;
    }
    .form-group {
      margin-bottom: 15px;
      width: 100%;
    }
    .form-group label {
      margin-bottom: 5px;
      text-align: left;
      display: block;
    }
    select, input[type="submit"] {
      padding: 8px;
      border-radius: 4px;
      border: 1px solid #ccc;
      width: 100%;
    }
    input[type="submit"] {
      background-color: #007bff;
      color: white;
      border: none;
      cursor: pointer;
      margin-top: 20px;
    }
    input[type="submit"]:hover {
      background-color: #0056b3;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
    }
    th, td {
      padding: 10px;
      border: 1px solid #ddd;
    }
    th {
      background-color: #f2f2f2;
    }
  </style>
</head>
<body>
  <div class="container">
    <h2>Browse awards based on Covid-status and Outlayed Amount</h2>

    <form method="post" id="list__header_select" class="list__header_select">
      <div class="form-group">
        <label for="amount_range">Select Outlayed Amount Range</label>
        <select name="amount_range" id="amount_range" required>
          <option value="0-5000000">0-5000000</option>
          <option value="5000001-10000000">5000001-10000000</option>
          <option value="10000001-15000000">10000001-15000000</option>
          <option value="15000001-20000000">15000001-20000000</option>
          <option value="20000001-25000000">20000001-25000000</option>
          <option value="25000001+">25000001+</option>
        </select>
      </div>
      <div class="form-group">
        <label for="covid_status">Select Covid Status</label>
        <select name="covid_status" id="covid_status" required>
          <option value="0">View All</option>
          <option value="1">Covid-related</option>
          <option value="2">Non Covid-related</option>
          <option value="3">Both</option>
        </select>
      </div>
      <input type="submit" name="submit" value="View Results">
    </form>

    <?php
    if (isset($_POST['submit'])) {
      if ($result) { ?>
        <h2>Results</h2>
        <table>
          <thead>
            <tr>
              <th>Prime Award ID</th>
            </tr>
          </thead>
          <tbody>
            <?php foreach ($result as $row) { ?>
              <tr>
                <td><?php echo htmlspecialchars($row["AwardID"]); ?></td>
              </tr>
            <?php } ?>
          </tbody>
        </table>
      <?php } else { ?>
        <p>No results found for the selected criteria.</p>
      <?php }
    }
    ?>
  </div>
</body>
</html>

<?php include('footer.php'); ?>
