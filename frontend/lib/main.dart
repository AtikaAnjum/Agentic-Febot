import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';
import 'package:intl/intl.dart';
import 'services/api_client.dart';

void main() {
  runApp(const SheGuardiaApp());
}

class SheGuardiaApp extends StatelessWidget {
  const SheGuardiaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'SheGuardia',
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0A0A0F),
        useMaterial3: true,
      ),
      home: const ChatScreen(),
    );
  }
}

class ChatMessage {
  final String role;
  final String content;
  final DateTime timestamp;
  ChatMessage({required this.role, required this.content, DateTime? timestamp})
    : timestamp = timestamp ?? DateTime.now();
}

class IncidentReport {
  String? incidentType;
  String? location;
  String? dateTime;
  String? description;
  String? suspectDescription;
  String? witnessInfo;
  String? additionalDetails;

  IncidentReport({
    this.incidentType,
    this.location,
    this.dateTime,
    this.description,
    this.suspectDescription,
    this.witnessInfo,
    this.additionalDetails,
  });

  bool get isComplete =>
      incidentType != null &&
      incidentType!.isNotEmpty &&
      location != null &&
      location!.isNotEmpty &&
      dateTime != null &&
      dateTime!.isNotEmpty &&
      description != null &&
      description!.isNotEmpty;
}

class ChatSession {
  final String id;
  final String title;
  final List<ChatMessage> messages;
  final DateTime lastUpdated;
  final IncidentReport incidentReport;
  final bool isIncidentReporting;

  ChatSession({
    required this.id,
    required this.title,
    required this.messages,
    required this.lastUpdated,
    required this.incidentReport,
    this.isIncidentReporting = false,
  });
}

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  late ChatSession _chatSession;
  bool _isSending = false;
  final ApiClient _api = ApiClient();
  late IncidentReport _incidentReport;
  bool _isIncidentReporting = false;
  int _reportStep = 0;

  @override
  void initState() {
    super.initState();
    _incidentReport = IncidentReport();
    _initializeNewChat();
  }

  void _initializeNewChat() {
    setState(() {
      _chatSession = ChatSession(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        title: 'New Chat',
        messages: [],
        lastUpdated: DateTime.now(),
        incidentReport: _incidentReport,
        isIncidentReporting: _isIncidentReporting,
      );
    });
  }

  void _startNewChat() {
    setState(() {
      _controller.clear();
      _incidentReport = IncidentReport();
      _isIncidentReporting = false;
      _reportStep = 0;
      _initializeNewChat();
    });
  }

  void _deleteChat() async {
    final confirm =
        await showDialog<bool>(
          context: context,
          builder:
              (ctx) => AlertDialog(
                title: const Text('Delete Chat?'),
                content: const Text(
                  'This will clear the current conversation and incident report.',
                ),
                actions: [
                  TextButton(
                    onPressed: () => Navigator.of(ctx).pop(false),
                    child: const Text('Cancel'),
                  ),
                  TextButton(
                    onPressed: () => Navigator.of(ctx).pop(true),
                    child: const Text('Delete'),
                  ),
                ],
              ),
        ) ??
        false;

    if (confirm) {
      _startNewChat();
    }
  }

  Future<void> _sendMessage(String text) async {
    if (text.trim().isEmpty || _isSending) return;

    setState(() {
      _chatSession.messages.add(
        ChatMessage(role: 'user', content: text.trim()),
      );
      _isSending = true;
    });
    _controller.clear();

    if (_chatSession.messages.length == 1) {
      _chatSession = ChatSession(
        id: _chatSession.id,
        title:
            text.trim().length > 30
                ? '${text.trim().substring(0, 30)}...'
                : text.trim(),
        messages: _chatSession.messages,
        lastUpdated: DateTime.now(),
        incidentReport: _incidentReport,
        isIncidentReporting: _isIncidentReporting,
      );
    }

    try {
      final response = await _api.post(
        '/chat',
        body: <String, dynamic>{
          'message': text.trim(),
          'conversation_history':
              _chatSession.messages
                  .map(
                    (m) => <String, String>{
                      'role': m.role,
                      'content': m.content,
                    },
                  )
                  .toList(),
        },
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = jsonDecode(response.body);
        final String botReply = data['response'] as String? ?? 'No response';
        setState(() {
          _chatSession.messages.add(
            ChatMessage(role: 'assistant', content: botReply),
          );
        });
      } else {
        setState(() {
          _chatSession.messages.add(
            ChatMessage(
              role: 'assistant',
              content:
                  'Sorry, I could not reach the server (code ${response.statusCode}).',
            ),
          );
        });
      }
    } catch (e) {
      setState(() {
        _chatSession.messages.add(
          ChatMessage(role: 'assistant', content: 'Network error: $e'),
        );
      });
    } finally {
      if (mounted) {
        setState(() {
          _isSending = false;
          _chatSession = ChatSession(
            id: _chatSession.id,
            title: _chatSession.title,
            messages: _chatSession.messages,
            lastUpdated: DateTime.now(),
            incidentReport: _incidentReport,
            isIncidentReporting: _isIncidentReporting,
          );
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF1A1A2E), Color(0xFF0A0A0F)],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              _buildChatHeader(),
              Expanded(
                child:
                    _chatSession.messages.isEmpty
                        ? _buildWelcomeScreen()
                        : _buildMessageList(),
              ),
              _buildInputBar(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildChatHeader() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1E1E2E).withOpacity(0.5),
        border: Border(
          bottom: BorderSide(color: Colors.white.withOpacity(0.05)),
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF7B2FF7), Color(0xFFFF5F6D)],
              ),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(Icons.security, color: Colors.white, size: 24),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                Text(
                  'SheGuardia',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                Text(
                  'Your Safety Companion • Online',
                  style: TextStyle(fontSize: 12, color: Colors.white60),
                ),
              ],
            ),
          ),
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_vert, color: Colors.white70),
            onSelected: (value) async {
              switch (value) {
                case 'new_chat':
                  _startNewChat();
                  break;
                case 'delete_chat':
                  _deleteChat();
                  break;
                case 'report':
                  _openIncidentReportSheet();
                  break;
                case 'pdf':
                  await _exportIncidentPdf();
                  break;
              }
            },
            itemBuilder:
                (context) => <PopupMenuEntry<String>>[
                  const PopupMenuItem<String>(
                    value: 'new_chat',
                    child: Text('New Chat'),
                  ),
                  const PopupMenuItem<String>(
                    value: 'delete_chat',
                    child: Text('Delete Chat'),
                  ),
                  const PopupMenuItem<String>(
                    value: 'report',
                    child: Text('Start Incident Report'),
                  ),
                  PopupMenuItem<String>(
                    value: 'pdf',
                    enabled: _incidentReport.isComplete,
                    child: Text(
                      _incidentReport.isComplete
                          ? 'Export Incident PDF'
                          : 'Export Incident PDF (incomplete)',
                    ),
                  ),
                ],
          ),
        ],
      ),
    );
  }

  Widget _buildWelcomeScreen() {
    return SingleChildScrollView(
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(
            16.0,
          ), // Reduced padding to fit smaller screens
          child: Column(
            mainAxisSize:
                MainAxisSize.min, // Use min to avoid taking full height
            children: [
              Container(
                padding: const EdgeInsets.all(24), // Reduced padding
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: LinearGradient(
                    colors: [
                      const Color(0xFF7B2FF7).withOpacity(0.3),
                      const Color(0xFFFF5F6D).withOpacity(0.3),
                    ],
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF7B2FF7).withOpacity(0.3),
                      blurRadius: 20,
                      spreadRadius: 3,
                    ),
                  ],
                ),
                child: const Icon(
                  Icons.security,
                  size: 48,
                  color: Colors.white,
                ), // Reduced icon size
              ),
              const SizedBox(height: 16),
              const Text(
                'Welcome to SheGuardia',
                style: TextStyle(
                  fontSize: 20, // Reduced font size
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              const Text(
                'Your safety companion is here to assist you.\nAsk anything or report an incident.',
                style: TextStyle(
                  fontSize: 14, // Reduced font size
                  color: Colors.white60,
                  height: 1.5,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              _buildSuggestionChips(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSuggestionChips() {
    final suggestions = [
      'I need emergency help',
      'Safety tips',
      'Report an incident',
    ];

    return ConstrainedBox(
      constraints: const BoxConstraints(
        maxWidth: 280,
      ), // Constrain width to prevent overflow
      child: Wrap(
        spacing: 8,
        runSpacing: 8,
        alignment: WrapAlignment.center,
        children:
            suggestions.map((suggestion) {
              return GestureDetector(
                onTap: () => _sendMessage(suggestion),
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 8,
                  ), // Reduced padding
                  decoration: BoxDecoration(
                    color: const Color(0xFF1E1E2E),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: const Color(0xFF7B2FF7).withOpacity(0.3),
                    ),
                  ),
                  child: Text(
                    suggestion,
                    style: const TextStyle(
                      color: Colors.white70,
                      fontSize: 12,
                    ), // Reduced font size
                  ),
                ),
              );
            }).toList(),
      ),
    );
  }

  Widget _buildMessageList() {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _chatSession.messages.length + (_isSending ? 1 : 0),
      itemBuilder: (context, index) {
        if (_isSending && index == _chatSession.messages.length) {
          return _buildTypingIndicator();
        }
        final message = _chatSession.messages[index];
        return _buildMessageBubble(message);
      },
    );
  }

  Widget _buildMessageBubble(ChatMessage message) {
    final isUser = message.role == 'user';
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        mainAxisAlignment:
            isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser) ...[
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF7B2FF7), Color(0xFFFF5F6D)],
                ),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.security, color: Colors.white, size: 20),
            ),
            const SizedBox(width: 12),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color:
                    isUser
                        ? const Color(0xFF7B2FF7).withOpacity(0.2)
                        : const Color(0xFF1E1E2E),
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(20),
                  topRight: const Radius.circular(20),
                  bottomLeft: Radius.circular(isUser ? 20 : 4),
                  bottomRight: Radius.circular(isUser ? 4 : 20),
                ),
                border: Border.all(
                  color:
                      isUser
                          ? const Color(0xFF7B2FF7).withOpacity(0.3)
                          : Colors.white.withOpacity(0.05),
                ),
              ),
              child: Text(
                message.content,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 15,
                  height: 1.4,
                ),
              ),
            ),
          ),
          if (isUser) ...[
            const SizedBox(width: 12),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: const Color(0xFF7B2FF7).withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: const Color(0xFF7B2FF7).withOpacity(0.3),
                ),
              ),
              child: const Icon(
                Icons.person,
                color: Color(0xFF7B2FF7),
                size: 20,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildTypingIndicator() {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF7B2FF7), Color(0xFFFF5F6D)],
              ),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(Icons.security, color: Colors.white, size: 20),
          ),
          const SizedBox(width: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: const Color(0xFF1E1E2E),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: const [
                _Dot(delay: 0),
                SizedBox(width: 4),
                _Dot(delay: 150),
                SizedBox(width: 4),
                _Dot(delay: 300),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInputBar() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1E1E2E).withOpacity(0.5),
        border: Border(top: BorderSide(color: Colors.white.withOpacity(0.05))),
      ),
      child: Row(
        children: [
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: const Color(0xFF0A0A0F),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: Colors.white.withOpacity(0.1)),
              ),
              child: TextField(
                controller: _controller,
                enabled: !_isSending,
                style: const TextStyle(color: Colors.white),
                decoration: const InputDecoration(
                  hintText: 'Type your message...',
                  hintStyle: TextStyle(color: Colors.white38),
                  border: InputBorder.none,
                  contentPadding: EdgeInsets.symmetric(
                    horizontal: 20,
                    vertical: 12,
                  ),
                ),
                onSubmitted: _sendMessage,
              ),
            ),
          ),
          const SizedBox(width: 12),
          GestureDetector(
            onTap: _isSending ? null : () => _sendMessage(_controller.text),
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF7B2FF7), Color(0xFFFF5F6D)],
                ),
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF7B2FF7).withOpacity(0.4),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: const Icon(
                Icons.send_rounded,
                color: Colors.white,
                size: 20,
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _openIncidentReportSheet() {
    setState(() {
      _isIncidentReporting = true;
      _reportStep = 0;
    });

    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF1E1E2E),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) {
        final incidentTypeController = TextEditingController(
          text: _incidentReport.incidentType ?? '',
        );
        final locationController = TextEditingController(
          text: _incidentReport.location ?? '',
        );
        final dateTimeController = TextEditingController(
          text:
              _incidentReport.dateTime ??
              DateFormat('yyyy-MM-dd HH:mm').format(DateTime.now()),
        );
        final descriptionController = TextEditingController(
          text: _incidentReport.description ?? '',
        );
        final suspectController = TextEditingController(
          text: _incidentReport.suspectDescription ?? '',
        );
        final witnessController = TextEditingController(
          text: _incidentReport.witnessInfo ?? '',
        );
        final additionalController = TextEditingController(
          text: _incidentReport.additionalDetails ?? '',
        );

        return StatefulBuilder(
          builder: (context, setSheetState) {
            Widget buildField(
              String label,
              TextEditingController controller, {
              int maxLines = 1,
            }) {
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label, style: const TextStyle(color: Colors.white70)),
                  const SizedBox(height: 8),
                  TextField(
                    controller: controller,
                    maxLines: maxLines,
                    style: const TextStyle(color: Colors.white),
                    decoration: InputDecoration(
                      filled: true,
                      fillColor: const Color(0xFF0A0A0F),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                  ),
                ],
              );
            }

            List<Widget> steps = [
              buildField('Incident Type', incidentTypeController),
              buildField('Location', locationController),
              buildField('Date & Time', dateTimeController),
              buildField('Description', descriptionController, maxLines: 4),
              buildField('Suspect Description', suspectController, maxLines: 3),
              buildField('Witness Info', witnessController, maxLines: 3),
              buildField(
                'Additional Details',
                additionalController,
                maxLines: 3,
              ),
            ];

            return Padding(
              padding: EdgeInsets.only(
                left: 16,
                right: 16,
                top: 16,
                bottom: MediaQuery.of(context).viewInsets.bottom + 16,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 40,
                    height: 4,
                    margin: const EdgeInsets.only(bottom: 16),
                    decoration: BoxDecoration(
                      color: Colors.white12,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                  const Text(
                    'Incident Report',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 16),
                  steps[_reportStep],
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      TextButton(
                        onPressed:
                            _reportStep > 0
                                ? () => setSheetState(() => _reportStep -= 1)
                                : null,
                        child: const Text('Back'),
                      ),
                      const Spacer(),
                      TextButton(
                        onPressed:
                            _reportStep < steps.length - 1
                                ? () => setSheetState(() => _reportStep += 1)
                                : null,
                        child: const Text('Next'),
                      ),
                      const SizedBox(width: 8),
                      ElevatedButton(
                        onPressed: () {
                          setState(() {
                            _incidentReport = IncidentReport(
                              incidentType:
                                  incidentTypeController.text.isNotEmpty
                                      ? incidentTypeController.text
                                      : null,
                              location:
                                  locationController.text.isNotEmpty
                                      ? locationController.text
                                      : null,
                              dateTime:
                                  dateTimeController.text.isNotEmpty
                                      ? dateTimeController.text
                                      : null,
                              description:
                                  descriptionController.text.isNotEmpty
                                      ? descriptionController.text
                                      : null,
                              suspectDescription:
                                  suspectController.text.isNotEmpty
                                      ? suspectController.text
                                      : null,
                              witnessInfo:
                                  witnessController.text.isNotEmpty
                                      ? witnessController.text
                                      : null,
                              additionalDetails:
                                  additionalController.text.isNotEmpty
                                      ? additionalController.text
                                      : null,
                            );
                            _isIncidentReporting = false;
                            _chatSession = ChatSession(
                              id: _chatSession.id,
                              title: _chatSession.title,
                              messages: _chatSession.messages,
                              lastUpdated: DateTime.now(),
                              incidentReport: _incidentReport,
                              isIncidentReporting: _isIncidentReporting,
                            );
                          });
                          Navigator.pop(context);
                        },
                        child: const Text('Save'),
                      ),
                    ],
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  Future<void> _exportIncidentPdf() async {
    if (!_incidentReport.isComplete) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Complete incident report first.')),
      );
      return;
    }

    final doc = pw.Document();
    final nowStr = DateFormat('yyyy-MM-dd HH:mm').format(DateTime.now());
    doc.addPage(
      pw.Page(
        pageFormat: PdfPageFormat.a4,
        build: (pw.Context ctx) {
          return pw.Padding(
            padding: const pw.EdgeInsets.all(24),
            child: pw.Column(
              crossAxisAlignment: pw.CrossAxisAlignment.start,
              children: [
                pw.Text(
                  'SheGuardia Incident Report',
                  style: pw.TextStyle(
                    fontSize: 22,
                    fontWeight: pw.FontWeight.bold,
                  ),
                ),
                pw.SizedBox(height: 8),
                pw.Text('Generated: $nowStr'),
                pw.SizedBox(height: 16),
                pw.Divider(),
                pw.SizedBox(height: 8),
                pw.Text(
                  'Incident Details',
                  style: pw.TextStyle(
                    fontSize: 16,
                    fontWeight: pw.FontWeight.bold,
                  ),
                ),
                pw.SizedBox(height: 8),
                pw.Bullet(
                  text: 'Type: ${_incidentReport.incidentType ?? 'N/A'}',
                ),
                pw.Bullet(
                  text: 'Location: ${_incidentReport.location ?? 'N/A'}',
                ),
                pw.Bullet(
                  text: 'Date & Time: ${_incidentReport.dateTime ?? 'N/A'}',
                ),
                pw.SizedBox(height: 8),
                pw.Text('Description:'),
                pw.Text(_incidentReport.description ?? 'N/A'),
                pw.SizedBox(height: 8),
                pw.Text('Suspect Description:'),
                pw.Text(_incidentReport.suspectDescription ?? 'N/A'),
                pw.SizedBox(height: 8),
                pw.Text('Witness Info:'),
                pw.Text(_incidentReport.witnessInfo ?? 'N/A'),
                pw.SizedBox(height: 8),
                pw.Text('Additional Details:'),
                pw.Text(_incidentReport.additionalDetails ?? 'N/A'),
                pw.SizedBox(height: 16),
                pw.Divider(),
                pw.SizedBox(height: 8),
                pw.Text(
                  'Chat Transcript',
                  style: pw.TextStyle(
                    fontSize: 16,
                    fontWeight: pw.FontWeight.bold,
                  ),
                ),
                pw.SizedBox(height: 8),
                pw.Column(
                  crossAxisAlignment: pw.CrossAxisAlignment.start,
                  children:
                      _chatSession.messages.map((m) {
                        final ts = DateFormat('HH:mm').format(m.timestamp);
                        return pw.Padding(
                          padding: const pw.EdgeInsets.only(bottom: 6),
                          child: pw.Text('[${m.role}] $ts: ${m.content}'),
                        );
                      }).toList(),
                ),
              ],
            ),
          );
        },
      ),
    );

    await Printing.layoutPdf(
      onLayout: (PdfPageFormat format) async => doc.save(),
    );
  }
}

class _Dot extends StatefulWidget {
  final int delay;
  const _Dot({this.delay = 0});

  @override
  State<_Dot> createState() => _DotState();
}

class _DotState extends State<_Dot> with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1200),
  )..repeat();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        final double t = (_controller.value + widget.delay / 1200) % 1.0;
        final double scale = 0.5 + 0.5 * (t < 0.5 ? t : 1 - t) * 2;
        return Transform.scale(
          scale: scale,
          child: Container(
            width: 6,
            height: 6,
            decoration: const BoxDecoration(
              color: Colors.white60,
              shape: BoxShape.circle,
            ),
          ),
        );
      },
    );
  }
}
