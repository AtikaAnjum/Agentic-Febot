import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiClient {
  ApiClient();

  // Choose sensible defaults per platform. Override with --dart-define=BACKEND_URL.
  static final String _defaultBase = _detectDefaultBaseUrl();
  static final String _baseUrl =
      const String.fromEnvironment('BACKEND_URL', defaultValue: '').isNotEmpty
          ? const String.fromEnvironment('BACKEND_URL')
          : _defaultBase;

  static String _detectDefaultBaseUrl() {
    // Default to localhost which works for web/desktop/iOS simulator
    // Android emulator needs 10.0.2.2, so override with --dart-define
    return 'http://localhost:8000';
    // return 'http://192.168.0.127:8000';
    // return 'http://192.168.100.7:8000';
    // return 'http://10.76.231.222:8000';
    // return 'http://10.113.64.139:8000';
  }

  Uri _uri(String path, [Map<String, dynamic>? query]) {
    final String clean = path.startsWith('/') ? path : '/$path';
    return Uri.parse(_baseUrl + clean).replace(queryParameters: query);
  }

  Future<http.Response> get(String path, {Map<String, dynamic>? query}) async {
    final uri = _uri(path, query);
    return await http
        .get(uri, headers: _headers())
        .timeout(
          const Duration(seconds: 120), // Increased from 10 to 15 seconds
          onTimeout: () => http.Response('Request timeout', 408),
        );
  }

  Future<http.Response> post(
    String path, {
    Map<String, dynamic>? query,
    Map<String, dynamic>? body,
  }) async {
    final uri = _uri(path, query);
    return await http
        .post(
          uri,
          headers: _headers(),
          body: jsonEncode(body ?? <String, dynamic>{}),
        )
        .timeout(
          const Duration(
            seconds: 120,
          ), // Increased from 30 to 60 seconds for complex chat operations
          onTimeout: () => http.Response('Request timeout', 408),
        );
  }

  Map<String, String> _headers() => <String, String>{
    'Content-Type': 'application/json',
  };
}
