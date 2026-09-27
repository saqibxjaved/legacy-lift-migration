import java.sql.Connection;
import java.sql.DatabaseMetaData;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

public class MigrationOrchestrator {

    private final String sourceUrl;
    private final String sourceUser;
    private final String sourcePassword;
    private final String targetUrl;
    private final String targetUser;
    private final String targetPassword;

    public MigrationOrchestrator(String sourceUrl, String sourceUser, String sourcePassword,
                                String targetUrl, String targetUser, String targetPassword) {
        this.sourceUrl = sourceUrl;
        this.sourceUser = sourceUser;
        this.sourcePassword = sourcePassword;
        this.targetUrl = targetUrl;
        this.targetUser = targetUser;
        this.targetPassword = targetPassword;
    }

    public void orchestrate() throws SQLException, ClassNotFoundException {
        Class.forName("com.mysql.cj.jdbc.Driver");

        try (Connection sourceConnection = DriverManager.getConnection(sourceUrl, sourceUser, sourcePassword);
             Connection targetConnection = DriverManager.getConnection(targetUrl, targetUser, targetPassword)) {

            String sourceSchema = extractDatabaseName(sourceUrl);
            String targetSchema = extractDatabaseName(targetUrl);
            List<String> tables = listTables(sourceConnection);

            for (String tableName : tables) {
                migrateTable(sourceConnection, targetConnection, sourceSchema, targetSchema, tableName);
            }
        }
    }

    private void migrateTable(Connection sourceConnection, Connection targetConnection,
                             String sourceSchema, String targetSchema,
                             String tableName) throws SQLException {

        String sourceQualified = sourceSchema + ".`" + tableName + "`";
        String targetQualified = targetSchema + ".`" + tableName + "`";

        String createTableSql = "CREATE TABLE IF NOT EXISTS " + targetQualified + " LIKE " + sourceQualified;
        String clearTargetSql = "TRUNCATE TABLE " + targetQualified;
        String copyDataSql = "INSERT INTO " + targetQualified + " SELECT * FROM " + sourceQualified;

        try (Statement targetStatement = targetConnection.createStatement()) {
            targetStatement.executeUpdate(createTableSql);
            targetStatement.executeUpdate(clearTargetSql);
            targetStatement.executeUpdate(copyDataSql);
        }
    }

    private List<String> listTables(Connection connection) throws SQLException {
        List<String> tableNames = new ArrayList<>();
        DatabaseMetaData metadata = connection.getMetaData();

        try (ResultSet resultSet = metadata.getTables(null, null, "%", new String[]{"TABLE"})) {
            while (resultSet.next()) {
                String tableName = resultSet.getString("TABLE_NAME");
                if (!"schema_version".equalsIgnoreCase(tableName)) {
                    tableNames.add(tableName);
                }
            }
        }

        return tableNames;
    }

    private String extractDatabaseName(String url) {
        String[] sections = url.split("/");
        if (sections.length < 4) {
            throw new IllegalArgumentException("Invalid JDBC URL: " + url + ". Expected format: jdbc:mysql://host:port/database");
        }
        return sections[3].split("\\?")[0];
    }

    public static void main(String[] args) {
        if (args.length != 6) {
            System.out.println("Usage: java MigrationOrchestrator <sourceUrl> <sourceUser> <sourcePassword> <targetUrl> <targetUser> <targetPassword>");
            System.out.println("Example: java MigrationOrchestrator jdbc:mysql://localhost:3306/hotel root Sudhir@123 jdbc:mysql://localhost:3306/hotel_backup root Sudhir@123");
            return;
        }

        String sourceUrl = args[0];
        String sourceUser = args[1];
        String sourcePassword = args[2];
        String targetUrl = args[3];
        String targetUser = args[4];
        String targetPassword = args[5];

        try {
            MigrationOrchestrator orchestrator = new MigrationOrchestrator(
                    sourceUrl, sourceUser, sourcePassword,
                    targetUrl, targetUser, targetPassword
            );

            System.out.println("Starting migration orchestration...");
            orchestrator.orchestrate();
            System.out.println("Migration completed successfully.");

        } catch (Exception e) {
            System.err.println("Migration failed: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
